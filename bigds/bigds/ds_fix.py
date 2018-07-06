"""
Helper script for examining and fixing datasets.

Usage:
    ds.fix [options] list-versions <ds-id>
    ds.fix [options] replay-from <ds-id> <ds-version>
    ds.fix [options] unsafe-restore-tip <ds-id> <ds-version>
    ds.fix [options] restore-tip <ds-id> <ds-version>
    ds.fix [options] recover <ds-id>
    ds.fix [options] diagnose <ds-id> [<ds-version>]
    ds.fix [options] list-all-actions [--long] <ds-id>
    ds.fix [options] save-actions <ds-id> <ds-version> <filename>
    ds.fix [options] show-actions [--long] <filename>

Options:
    -i                      Run interactive prompt after the command
    --cr-lib-config=FILENAME
                            [default: /var/lib/crunch.io/cr.server-0.conf]
    --owner-email=EMAIL     [default: captain@crunch.io]
    --zz9repo=DIRNAME

Command summaries:
    list-versions       Print versions (savepoints) for a dataset.

    replay-from         Create a new dataset by replaying the actions of another
                        dataset starting at a savepoint.

    unsafe-restore-tip  Re-create the tip version of a dataset by replaying
                        actions starting at a savepoint. If anything goes wrong,
                        recovery is difficult or impossible.

    restore-tip         Re-create the tip version of a dataset by replaying
                        actions starting at a savepoint. Before any changes are
                        made, the dataset's repository directory is backed up
                        and the actions are saved to a pickle file.

    recover             Attempt to recover a dataset to the way it was before
                        the restore-tip command was run, using the repo back dir
                        and the pickle file with saved actions. If something is
                        wrong with the backup, this could make things worse than
                        before.

WARNING!!! these commands are currently experimental and/or dangerous.
"""
from __future__ import print_function
import datetime
import errno
import itertools
import os
from os.path import join
import pprint
import subprocess
import sys
import tempfile
import time

import docopt
import six
from six.moves import cPickle as pickle

from cr.lib.commands.common import load_settings, startup
from cr.lib import actions as actionslib
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib.entities.datasets.versions.versioning import (
    version_health,
    VersionTag,
)
from cr.lib.entities.users import User
from cr.lib.settings import settings
from cr.lib import stores

this_module = sys.modules[__name__]


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args['--cr-lib-config']
    settings.update(load_settings(settings_yaml))
    startup()


def do_list_versions(args):
    ds_id = args['<ds-id>']
    _cr_lib_init(args)
    version_list = version_health(ds_id)
    print(len(version_list), "versions:")
    for version_id, version_info in version_list:
        print("{:32} {}".format(version_id, version_info['date']))
    return {
        'ds_id': ds_id,
        'version_list': version_list,
    }


def do_replay_from(args):
    ds_id = args['<ds-id>']
    ds_version = args['<ds-version>']
    _cr_lib_init(args)
    source_dataset = Dataset.find_one_with_timeout(
        dict(id=ds_id, version='master__tip'), timeout=5, wait=0.5)
    newds_id = stores.gen_id()
    dataset_name = "REPLAY: " + source_dataset.name
    dataset_owner = User.get_by_email(args['--owner-email'])
    newds = Dataset(
        id=newds_id,
        name=dataset_name,
        owner_type='User',
        owner_id=dataset_owner.id,
    )
    newds.replay_from(source_dataset, from_version=ds_version, task=None)
    print("Created new dataset by replaying dataset", ds_id, "from savepoint",
          ds_version)
    print("New dataset ID:", newds.id)
    print("New dataset Name:", newds.name)


def do_unsafe_restore_tip(args):
    """
    Remove the master__tip version of dataset <ds-id> and re-create it by
    re-playing actions starting at savepoint <ds-version>.
    No "safety-net" is provided if replaying fails - the master__tip version
    will be lost or corrupted.
    """
    ds_id = args['<ds-id>'].strip()
    ds_version = args['<ds-version>'].strip()
    assert ds_id and ds_version
    _cr_lib_init(args)
    target_ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    print("About to call: _unsafe_restore_tip({!r}, {!r})"
          .format(target_ds, ds_version))
    _unsafe_restore_tip(target_ds, ds_version)
    print("Done.")


def _unsafe_restore_tip(target_ds, from_version):
    """
    target_ds: Dataset that will have it's tip re-created
    from_version: 'master__<revision>' version to replay from
    """
    from_branch = Dataset.version_branch(from_version)
    from_revision = Dataset.version_revision(from_version)
    if from_branch != target_ds.branch:
        raise ValueError(
            'Start and End versions of replay must be on same branch.')
    with actionslib.dataset_lock('unsafe_restore_tip', target_ds.id,
                                 dataset_branch=target_ds.branch,
                                 exclusive=True):
        vtag = VersionTag.nearest(target_ds.id, from_branch, from_revision)
        if vtag is None or vtag.revision(vtag.version) != from_revision:
            raise ValueError('There is no savepoint at that revision')

        # Grab delta from that savepoint up to <branch>__tip
        savepoint_action = vtag.action
        actions_to_replay = actionslib.for_dataset(
            target_ds, None, since=savepoint_action, only_successful=True,
            exclude_hashes=[savepoint_action.hash], replay_order=True
        )

        # Revert from <branch>__tip back to the savepoint.
        # This also deletes the actions between the savepoint and tip.
        target_ds.restore_savepoint(vtag)

        # Replay those actions to get the dataset back the way it was.
        target_ds.play_workflow(
            None,
            actions_to_replay,
            autorollback=target_ds.AutorollbackType.Disabled,
            task=None,
        )


def do_restore_tip(args):
    """
    Restore the tip of a dataset by replaying from a savepoint.
    This is intended to be safer than unsafe-restore-tip in that before
    reverting to a savepoint it takes these steps:
        - Save the actions that will be deleted to a pickle file.
        - Back up the zz9repo directory (this could take a while!)
    All of this is done in the context of a dataset lock.
    If this process is interrupted or crashes, the ds.recover command is
    intended to get back to the original state using the backups of the actions
    and repo directory.
    """
    ds_id = args['<ds-id>'].strip()
    ds_version = args['<ds-version>'].strip()
    assert ds_id and ds_version
    zz9repo_base = args['--zz9repo']
    if not zz9repo_base:
        raise ValueError(
            "--zz9repo parameter required to find and backup repo dir")
    if not os.path.isdir(zz9repo_base):
        raise ValueError(
            "Invalid --zz9repo parameter: Not a directory.")
    zz9repo_dir = join(zz9repo_base, ds_id[:2], ds_id)
    if not os.path.isdir(zz9repo_dir):
        raise ValueError(
            "No such dataset repository dir: {}".format(zz9repo_dir))
    _cr_lib_init(args)
    target_ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    _restore_tip(target_ds, ds_version, zz9repo_dir)
    print("Done.")


def _open_unique_file(prefix, suffix='.dat', dir=None):
    if not dir:
        dir = os.getcwd()
    timestamp = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    f = tempfile.NamedTemporaryFile(mode='w',
                                    prefix=prefix + '-' + timestamp + '-',
                                    suffix=suffix,
                                    dir=dir,
                                    delete=False)
    os.chmod(f.name, 0o664)
    return f


def _create_empty_backup_dir(dirpath):
    dirname = os.path.basename(dirpath)
    for i in itertools.count():
        backup_dirpath = "{}-bak{:03}".format(dirpath, i)
        try:
            os.mkdir(backup_dirpath)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise
        else:
            return backup_dirpath


def _restore_tip(target_ds, from_version, zz9repo_dir):
    from_branch = Dataset.version_branch(from_version)
    from_revision = Dataset.version_revision(from_version)
    if from_branch != target_ds.branch:
        raise ValueError(
            'Start and End versions of replay must be on same branch.')
    if os.path.basename(zz9repo_dir) != target_ds.id:
        raise ValueError("repo dir {} doesn't seem to match dataset ID {}"
                         .format(zz9repo_dir), target_ds.id)
    print("Locking dataset", target_ds.id, "branch", target_ds.branch)
    with actionslib.dataset_lock('restore_tip', target_ds.id,
                                 dataset_branch=target_ds.branch,
                                 exclusive=True):
        print("Finding the savepoint at branch", from_branch, "revision",
              from_revision)
        vtag = VersionTag.nearest(target_ds.id, from_branch, from_revision)
        if vtag is None or vtag.revision(vtag.version) != from_revision:
            raise ValueError('There is no savepoint at that revision')

        # Grab delta from that savepoint up to <branch>__tip
        savepoint_action = vtag.action
        actions_to_replay = actionslib.for_dataset(
            target_ds, None, since=savepoint_action, only_successful=True,
            exclude_hashes=[savepoint_action.hash], replay_order=True
        )

        # save actions to file
        with _open_unique_file('actions') as f:
            print("Saving", len(actions_to_replay), "actions to", f.name)
            pickle.dump(actions_to_replay, f, 2)

        # backup dataset repo dir
        backup_zz9repo_dir = _create_empty_backup_dir(zz9repo_dir)
        print("Backing up repository directory to", backup_zz9repo_dir)
        cmd = ['cp', '-pR']
        cmd.extend([join(zz9repo_dir, i) for i in os.listdir(zz9repo_dir)])
        assert len(cmd) >= 3
        cmd.append(backup_zz9repo_dir + '/')
        print(subprocess.list2cmdline(cmd))
        subprocess.check_call(cmd)

        # Revert from <branch>__tip back to the savepoint.
        # This also deletes the actions between the savepoint and tip.
        print("Reverting to savepoint", vtag)
        target_ds.restore_savepoint(vtag)

        # Replay those actions to get the dataset back the way it was.
        print("Replaying actions")
        target_ds.play_workflow(
            None,
            actions_to_replay,
            autorollback=target_ds.AutorollbackType.Disabled,
            task=None,
        )
    print("Done.")


def do_diagnose(args):
    ds_id = args['<ds-id>']
    ds_version = args['<ds-version>'] or 'master__tip'
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version=ds_version)
    info = ds.diagnose()
    pprint.pprint(info)
    _check_ds_diagnosis(info)


def _check_ds_diagnosis(info, format=None):
    if info['writeflag']:
        raise Exception("Non-empty writeflag present.")
    if format:
        if str(info['format']) != str(format):
            raise Exception("Format {} in diagnosis doesn't match format {}"
                            .format(info['format'], format))
    errors = _check_dict_for_errors(info)
    if errors:
        raise Exception("Errors found in diagnosis: {}".format(errors))


def _check_dict_for_errors(d, path=None, errors=None):
    if path is None:
        path = []
    if errors is None:
        errors = []
    for key, value in d.items():
        if key in ('error', 'errors'):
            if value:
                errors.append(('.'.join(str(i) for i in (path + [key])),
                              value))
        elif isinstance(value, dict):
            _check_dict_for_errors(value, path=(path + [key]), errors=errors)
    return errors


def test_check_dict_for_errors():
    d0 = {
        'blah': [1, 2, 3],
        'blee': {'bloo': {'msg': "all is well"}},
    }
    d1 = {
        'blah': [1, 2, 3],
        'blee': {'error': None},
    }
    d2 = {
        'blah': [1, 2, 3],
        'blee': {'error': "Red alert!"},
    }
    d3 = {
        'blah': [1, 2, 3],
        'blee': {'errors': ['e1', 'e2', 'e3']},
        'error': 4,
    }
    assert _check_dict_for_errors(d0) == []
    assert _check_dict_for_errors(d1) == []
    assert _check_dict_for_errors(d2) == [('blee.error', 'Red alert!')]
    e = _check_dict_for_errors(d3)
    assert len(e) == 2
    assert ('blee.errors', ['e1', 'e2', 'e3']) in e
    assert ('error', 4) in e


def do_list_all_actions(args):
    """
    List all actions for a dataset in chronological order
    """
    ds_id = args['<ds-id>']
    ds_version = 'master__tip'
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version=ds_version)
    history = actionslib.for_dataset(ds, None, since=None, upto=None,
                                     replay_order=True, only_successful=True,
                                     exclude_keys=None)
    _print_action_list(args, history)
    return {
        'ds_id': ds_id,
        'ds': ds,
        'history': history,
    }


def do_show_actions(args):
    """Load a pickle file and print the actions saved in it."""
    filename = args['<filename>']
    with open(filename, 'rb') as f:
        history = pickle.load(f)
    _print_action_list(args, history)


def _print_action_list(args, history):
    print(len(history), "actions:")
    for action in history:
        if args['--long']:
            pprint.pprint(action)
        else:
            pprint.pprint(_abbreviate_action(action))


def do_save_actions(args):
    """
    Save all actions after a savepoint (skip the savepoint action itself.)
    The action list might be empty for a savepoint that is a copy of
    master__tip.
    """
    ds_id = args['<ds-id>']
    from_version = args['<ds-version>']
    filename = args['<filename>']
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    _save_actions(ds, from_version, filename)


def _save_actions(ds, from_version, filename):
    from_branch = Dataset.version_branch(from_version)
    from_revision = Dataset.version_revision(from_version)
    if from_branch != ds.branch:
        raise ValueError(
            'Start and End versions must be on same branch.')
    with actionslib.dataset_lock('save_actions', ds.id,
                                 dataset_branch=ds.branch,
                                 exclusive=False):
        vtag = VersionTag.nearest(ds.id, from_branch, from_revision)
        if vtag is None or vtag.revision(vtag.version) != from_revision:
            raise ValueError('There is no savepoint at that revision')

        # Grab delta from that savepoint up to <branch>__tip
        savepoint_action = vtag.action
        actions_to_save = actionslib.for_dataset(
            ds, None, since=savepoint_action, only_successful=True,
            exclude_hashes=[savepoint_action.hash], replay_order=True
        )
    print("Saving", len(actions_to_save), "actions to", filename)
    with open(filename, 'wb') as f:
        pickle.dump(actions_to_save, f, 2)


def _abbreviate_action(action):
    d = {}
    for key in ('key', 'utc', 'hash'):
        d[key] = action[key]
    params = action['params']
    d['params.dataset.id'] = params['dataset']['id']
    d['params.dataset.branch'] = params['dataset']['branch']
    return d


def _do_command(args):
    t0 = time.time()
    try:
        for key, value in six.iteritems(args):
            if not key.startswith('-') and not key.startswith('<') and value:
                funcname = 'do_' + key.replace('-', '_')
                func = getattr(this_module, funcname, None)
                if func:
                    return func(args)
        print("No command, or command not implemented yet.", file=sys.stderr)
        return 1
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


def main():
    args = docopt.docopt(__doc__)
    result = _do_command(args)
    namespace = {
        'args': args,
    }
    if isinstance(result, dict):
        namespace['exit_code'] = 0
        namespace.update(result)
    else:
        namespace['exit_code'] = result
    if args['-i']:
        try:
            import IPython
            IPython.start_ipython(argv=[], user_ns=namespace)
        except ImportError:
            import code
            code.interact(local=namespace)
    return namespace['exit_code']


if __name__ == '__main__':
    sys.exit(main())
