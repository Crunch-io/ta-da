"""
Helper script for finding and doing stuff with broken datasets

Usage:
    ds.fix [options] list-versions <ds-id>
    ds.fix [options] replay-from <ds-id> <ds-version>
    ds.fix [options] unsafe-restore-tip <ds-id> <ds-version>
    ds.fix [options] list-all-actions [--long] <ds-id>
    ds.fix [options] save-actions <ds-id> <ds-version> <filename>
    ds.fix [options] show-actions [--long] <filename>
    ds.fix [options] replay-actions <ds-id> <filename>

Options:
    -i                      Run interactive prompt after the command
    --cr-lib-config=FILENAME
                            [default: /var/lib/crunch.io/cr.server-0.conf]
    --owner-email=EMAIL     [default: captain@crunch.io]

WARNING!!! these commands are currently experimental and/or dangerous.
"""
from __future__ import print_function
import pprint
import sys
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
    target_ds = Dataset.find_one_with_timeout(
        dict(id=ds_id, version='master__tip'), timeout=5, wait=0.5)
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
    print(len(history), "actions:")
    for action in history:
        if args['--long']:
            pprint.pprint(action)
        else:
            pprint.pprint(_abbreviate_action(action))
    return {
        'ds_id': ds_id,
        'ds': ds,
        'history': history,
    }


def do_save_actions(args):
    """
    Save all actions after a savepoint (skip the savepoint action itself.)
    The action list might be empty for a savepoint that is a copy of
    master__tip.
    """
    ds_id = args['<ds-id>']
    ds_version = args['<ds-version>']
    filename = args['<filename>']
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version=ds_version)
    svp = VersionTag.nearest(ds.id, ds.branch, ds.revision)
    history = actionslib.for_dataset(ds, None, since=svp.action,
                                     upto=None, replay_order=True,
                                     only_successful=True, exclude_keys=None)
    # Skip the first action in the history because it is the savepoint action
    # itself.
    actions_list = history[1:]
    with open(filename, 'wb') as f:
        pickle.dump(actions_list, f, 2)
    return {
        'actions_list': actions_list,
        'ds_id': ds_id,
        'ds_version': ds_version,
        'ds': ds,
        'filename': filename,
        'history': history,
        'svp': svp,
    }


def do_show_actions(args):
    filename = args['<filename>']
    with open(filename, 'rb') as f:
        actions_list = pickle.load(f)
    print(len(actions_list), "actions:")
    for action in actions_list:
        if args['--long']:
            pprint.pprint(action)
        else:
            pprint.pprint(_abbreviate_action(action))
    return {
        'actions_list': actions_list,
        'filename': filename,
    }


def _abbreviate_action(action):
    d = {}
    for key in ('key', 'utc', 'hash'):
        d[key] = action[key]
    params = action['params']
    d['params.dataset.id'] = params['dataset']['id']
    d['params.dataset.branch'] = params['dataset']['branch']
    return d


def do_replay_actions(args):
    ds_id = args['<ds-id>']
    ds_version = 'master__tip'
    filename = args['<filename>']
    with open(filename, 'rb') as f:
        actions_list = pickle.load(f)
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version=ds_version)
    ds.play_workflow(None, actions_list,
                     autorollback=ds.AutorollbackType.Full)
    return {
        'actions_list': actions_list,
        'ds_id': ds_id,
        'ds_version': ds_version,
        'ds': ds,
    }


def do_restore_from_savepoint(args):
    ds_id = args['<ds-id>']
    ds_version = args['<ds-version>']
    if not ds_version:
        ds_version = 'master__tip'
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version=ds_version)
    ds_rollback_revision = ds.get_current_revision()
    print("Rolling back dataset", ds_id, "to revision", ds_rollback_revision)
    ds.rollback(ds_rollback_revision)
    return {
        'ds_id': ds_id,
        'ds_version': ds_version,
        'ds_rollback_revision': ds_rollback_revision,
        'ds': ds,
    }


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
