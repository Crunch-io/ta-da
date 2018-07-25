#!/usr/bin/env python
"""
Helper script for examining and fixing datasets.

Usage:
    ds.fix [options] list-versions <ds-id>
    ds.fix [options] replay-from <ds-id> [<ds-version>]
    ds.fix [options] restore-tip <ds-id> [<ds-version>]
    ds.fix [options] diagnose <ds-id> [<ds-version>]
    ds.fix [options] diagnose-fromfile <filename>
    ds.fix [options] list-actions <ds-id> [<ds-version>]
    ds.fix [options] save-actions <ds-id> <ds-version> <filename>
    ds.fix [options] save-all-actions <ds-id> <filename>
    ds.fix [options] show-actions <filename>
    ds.fix [options] apply-actions <ds-id> <filename> [--offset=N]

Options:
    -i                        Run interactive prompt after the command
    --long                    Output data in longer format if applicable.
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]
    --owner-email=EMAIL       Email address of new dataset owner when doing
                              replay-from. [default: captain@crunch.io]
    --backup-repo-dir         Back up dataset repo dir before doing restore-tip
    --zz9repo=DIRNAME         Location of root of zz9 repositories, used when
                              backing up dataset repo dir.
                              [default: /var/lib/crunch.io/zz9repo]
    --format=FORMAT           Expected zz9 format [default: 25]
    --include-failed          Also list or save actions that did not succeed
    --yes                     Bypass "Are you sure?" prompt on restore-tip
    --no-replay-from          Don't do the automatic replay-from when doing
                              restore-tip. Note: This is dangerous, and not
                              allowed if not restoring from a savepoint.

Command summaries:
    list-versions       Print versions (savepoints) for a dataset.

    replay-from         Create a new dataset by replaying the actions of another
                        dataset starting at a savepoint.

    restore-tip         Re-create the tip version of a dataset by replaying
                        actions starting at a savepoint. Before any changes are
                        made, the actions are saved to a pickle file.

WARNING!!! these commands are currently experimental and/or dangerous.
"""
from __future__ import print_function
from collections import OrderedDict
import datetime
import errno
import itertools
import json
import os
from os.path import basename, dirname, join, splitext
import pprint
import subprocess
import sys
import tempfile
import time
import traceback
import warnings

import docopt
from magicbus import bus
from magicbus.plugins import loggers
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
from cr.lib import exceptions
from cr.lib.index.indexer import index_dataset, index_dataset_variables
from cr.lib.loglib import log, log_to_stdout
from cr.lib.settings import settings
from cr.lib import stores
from zz9lib.errors import ZZ9Timeout

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
    try:
        version_list = version_health(ds_id)
    except ZZ9Timeout:
        print("Query timeout while getting version list for dataset {}"
              .format(ds_id))
        return 1
    print(len(version_list), "versions:")
    if args['--long']:
        for version_id, version_info in version_list:
            print("{}:".format(version_id))
            pprint.pprint(version_info)
    else:
        print("version-id                               ds ver date")
        print("---------------------------------------- -- ---", '-' * 19)
        for version_id, version_info in version_list:
            version_date = str(version_info['date'])
            print(
                "{:40} {:2} {:3} {:19}".format(
                    version_id,
                    version_info.get('datasets', 0),
                    version_info.get('version_tags', 0),
                    version_date,
                ),
            )
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
    owner_email = args['--owner-email']
    newds, succeeded = _replay_from(source_dataset, ds_version, owner_email)
    if newds is not None:
        if ds_version is not None:
            from_msg = "from savepoint {}".format(ds_version)
        else:
            from_msg = "from the beginning"
        print("Created new dataset by replaying dataset", ds_id, from_msg)
        print("New dataset ID:", newds.id)
        print("New dataset Name:", newds.name)
    print("Succeeded:", succeeded)
    return 0 if succeeded else 1


def _replay_from(source_dataset, from_version, owner_email):
    """
    Create a new dataset by replaying actions from source_dataset from savepoint
    from_version, or from the beginning if from_version is None.
    Return (newds, succeeded)
    """
    newds_id = stores.gen_id()
    dataset_name = "REPLAY: " + source_dataset.name
    try:
        dataset_owner = User.get_by_email(owner_email)
    except exceptions.NotFound:
        print('Owner email "{}" not found.'.format(owner_email),
              file=sys.stderr)
        return None, False
    newds = Dataset(
        id=newds_id,
        name=dataset_name,
        owner_type='User',
        owner_id=dataset_owner.id,
    )
    succeeded = True
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        try:
            newds.replay_from(source_dataset, from_version=from_version,
                              task=None)
        except Exception:
            succeeded = False
            traceback.print_exc()
    return newds, succeeded


def do_restore_tip(args):
    """
    Restore the tip of a dataset by replaying from a savepoint.
    This is intended to be safer than unsafe-restore-tip in that before
    reverting to a savepoint it takes these steps:
        - Save the actions that will be deleted to a pickle file.
        - Back up the zz9repo directory (this could take a while!)
    All of this is done in the context of a dataset lock.
    """
    ds_id = args['<ds-id>'].strip()
    assert ds_id
    ds_version = args['<ds-version>']
    zz9repo_base = args['--zz9repo']
    if args['--backup-repo-dir']:
        if not os.path.isdir(zz9repo_base):
            raise ValueError(
                "Invalid --zz9repo parameter: Not a directory: {}"
                .format(zz9repo_base))
        zz9repo_dir = join(zz9repo_base, ds_id[:2], ds_id)
    else:
        zz9repo_dir = None
    if not ds_version and args['--no-replay-from']:
        # Replaying entire history requires doing a delete first, which deletes
        # all the sources unless you have done a replay-from.
        raise ValueError("Cannot skip replay-from if restoring entire history.")
    if not args['--yes']:
        answer = six.moves.input(
            "About to modify a dataset. Are you sure? y/[n] ")
        if not answer.strip().lower().startswith('y'):
            print("Aborting.")
            return 1
    if ds_version:
        log.info("ds.fix restore-tip {} {}".format(ds_id, ds_version))
    else:
        log.info("ds.fix restore-tip {}".format(ds_id))
    _cr_lib_init(args)
    restorer = _DatasetTipRestorer(ds_id, ds_version, zz9repo_dir,
                                   no_replay_from=args['--no-replay-from'],
                                   owner_email=args['--owner-email'])
    succeeded = restorer()
    if succeeded:
        print("Done.")
        return 0
    else:
        print("Failed.")
        return 1


def _create_unique_file(prefix, suffix='.dat', dir=None):
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
    for i in itertools.count():
        backup_dirpath = "{}-bak{:03}".format(dirpath, i)
        try:
            os.mkdir(backup_dirpath)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise
        else:
            return backup_dirpath


class _DatasetTipRestorer(object):

    def __init__(self, ds_id, from_version, zz9repo_dir, no_replay_from=False,
                 owner_email=None):
        self.target_ds = Dataset.find_by_id(id=ds_id, version='master__tip')
        if zz9repo_dir:
            if os.path.basename(zz9repo_dir) != ds_id:
                raise ValueError(
                    "repo dir {} doesn't seem to match dataset ID {}"
                    .format(zz9repo_dir), ds_id)
            if not os.path.isdir(zz9repo_dir):
                raise ValueError(
                    "No such dataset repository dir: {}".format(zz9repo_dir))
        if from_version:
            from_branch = Dataset.version_branch(from_version)
            if from_branch != self.target_ds.branch:
                raise ValueError(
                    'Start and End versions of replay must be on same branch.')
        elif no_replay_from:
            raise ValueError(
                "Must do replay-from if restoring from entire history, "
                "because dataset gets deleted with its sources "
                "and sources will be lost if no other dataset using them.")
        self.from_version = from_version
        self.zz9repo_dir = zz9repo_dir
        self.no_replay_from = no_replay_from
        self.owner_email = owner_email
        #####
        self.restore_tip_filename = None
        self.actions_filename = None
        self.backup_zz9repo_dir = None
        self.replay_from_ds = None
        self.replay_from_succeeded = None
        self.datetime_started = None
        self.datetime_finished = None

    def __call__(self):
        self.datetime_started = datetime.datetime.utcnow()
        self._write_restore_tip_file()
        try:
            with actionslib.dataset_lock('restore_tip', self.target_ds.id,
                                         dataset_branch=self.target_ds.branch,
                                         exclusive=True):
                self._restore_savepoint()
            self.datetime_finished = datetime.datetime.utcnow()
            self._write_restore_tip_file(completed=True)
            return True
        except Exception:
            self.datetime_finished = datetime.datetime.utcnow()
            self._write_restore_tip_file(caught_exc=True)
            return False

    def _restore_savepoint(self):
        vtag, actions_to_replay = _get_vtag_actions_list(self.target_ds,
                                                         self.from_version)

        self._save_actions(actions_to_replay)
        if not self.zz9repo_dir:
            print("NOT backing up the repository directory.")
        else:
            self._backup_dataset_repo_dir()
        if not self.no_replay_from:
            if not self._preflight_replay_from():
                raise ValueError("Pre-flight dataset replay failed. Aborting.")

        if vtag is None:
            # Destroy this dataset so that we can recreate it from scratch
            # using the entire history.
            first_action = actions_to_replay[0]
            if first_action['key'] != 'Dataset.create':
                raise ValueError("First action is not Dataset.create; "
                                 "cannot re-create dataset from history.")
            actions_to_replay = actions_to_replay[1:]
            print("Destroying dataset {} so we can re-create it from history"
                  .format(self.target_ds.id))
            self.target_ds.destroy()
            _create_ds_from_first_action(self.target_ds, first_action)
        else:
            # Revert from <branch>__tip back to the savepoint.
            # This also deletes the actions between the savepoint and tip.
            print("Reverting to savepoint", vtag.version)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                self.target_ds.restore_savepoint(vtag)

        # Replay those actions to get the dataset back the way it was.
        print("Replaying", len(actions_to_replay), "actions")
        self.target_ds.play_workflow(
            None,
            actions_to_replay,
            autorollback=self.target_ds.AutorollbackType.LastAction,
            rehash=False,
            task=None,
        )

        print("Indexing dataset metadata and variables")
        index_dataset(self.target_ds)
        index_dataset_variables(self.target_ds)

    def _save_actions(self, actions_list):
        self.actions_filename = join(
            dirname(self.restore_tip_filename),
            splitext(basename(self.restore_tip_filename))[0] + '-actions.dat')
        with open(self.actions_filename, 'wb') as f:
            pickle.dump(actions_list, f, 2)

    def _backup_dataset_repo_dir(self):
        self.backup_zz9repo_dir = _create_empty_backup_dir(self.zz9repo_dir)
        print("Backing up repository directory to", self.backup_zz9repo_dir)
        cmd = ['cp', '-pR']
        cmd.extend([join(self.zz9repo_dir, i)
                    for i in os.listdir(self.zz9repo_dir)])
        assert len(cmd) >= 3
        cmd.append(self.backup_zz9repo_dir + '/')
        print(subprocess.list2cmdline(cmd))
        subprocess.check_call(cmd)

    def _preflight_replay_from(self):
        print("Doing pre-flight replay-from...", end=' ')
        newds, succeeded = _replay_from(self.target_ds,
                                        self.from_version,
                                        self.owner_email)
        self.replay_from_ds, self.replay_from_succeeded = newds, succeeded
        if succeeded:
            print("succeeded.", end=' ')
        else:
            print("failed.", end=' ')
        print("New dataset ID:", newds.id if newds is not None else None)
        return self.replay_from_succeeded

    def _write_restore_tip_file(self, completed=False, caught_exc=False):
        if caught_exc:
            error = traceback.format_exc()
            # Just in case we get an exception trying to write to the result
            # file, also send the error to stderr.
            sys.stderr.write(error)
            sys.stderr.write('\n')
        else:
            error = None
        if not self.restore_tip_filename:
            f = _create_unique_file("restore-tip-{}".format(self.target_ds.id),
                                    suffix='.json')
            self.restore_tip_filename = f.name
        else:
            f = open(self.restore_tip_filename, 'wb')
        if completed or caught_exc:
            print("Saving restore-tip parameters to:",
                  self.restore_tip_filename)
        try:
            params = OrderedDict([
                ('ds_id', self.target_ds.id),
                ('from_version', self.from_version),
                ('actions_filename', self.actions_filename),
                ('backup_zz9repo_dir', self.backup_zz9repo_dir),
                ('replay_from_ds_id', self.replay_from_ds.id if
                 self.replay_from_ds else None),
                ('replay_from_succeeded', self.replay_from_succeeded),
                ('completed', completed),
                ('error', error),
                ('datetime_started', self.datetime_started and
                 self.datetime_started.isoformat(' ')),
                ('datetime_finished', self.datetime_finished and
                 self.datetime_finished.isoformat(' ')),
            ])
            json.dump(params, f, indent=4, separators=(',', ': '))
            f.write('\n')
        finally:
            f.close()


def _create_ds_from_first_action(ds, first_action):
    print('Re-creating dataset {} "{}"'.format(ds.id, ds.name))
    _data = first_action['params'].get('_data', {})
    name = _data.get('name')
    description = _data.get('description')
    if name is not None:
        ds.name = name
    if description is not None:
        ds.description = description
    ds.create()


def _get_vtag_actions_list(ds, from_version, only_successful=True):
    """
    Get actions for a dataset starting at a savepoint going towards the tip, in
    replay order. If from_version is None then get all actions from the
    beginning and return None for vtag.
    Return (vtag, actions_list)
    vtag: VersionTag object
    """
    if from_version is not None:
        from_revision = Dataset.version_revision(from_version)
        vtag = VersionTag.nearest(ds.id, ds.branch, from_revision)
        if vtag is None or vtag.revision(vtag.version) != from_revision:
            raise ValueError('No such savepoint: {}'.format(from_revision))
        # Grab delta from that savepoint up to <branch>__tip
        since_action = vtag.action
        exclude_hashes = [since_action.hash]
    else:
        vtag = None
        since_action = None
        exclude_hashes = []
    actions_list = actionslib.for_dataset(
        ds, None, since=since_action, only_successful=only_successful,
        exclude_hashes=exclude_hashes, replay_order=True
    )
    return vtag, actions_list


def do_diagnose(args):
    ds_id = args['<ds-id>']
    ds_version = args['<ds-version>'] or 'master__tip'
    format = args['--format']
    _cr_lib_init(args)
    try:
        ds = Dataset.find_by_id(id=ds_id, version=ds_version)
    except exceptions.NotFound:
        print("Dataset version {}@{} not found.".format(ds_id, ds_version))
        return 1
    info = ds.diagnose()
    pprint.pprint(info)
    _check_ds_diagnosis(info, format)


def do_diagnose_fromfile(args):
    """
    The input file lines are in the format:
    <dataset-id> <version> <version>...
    If no <version> is given, master__tip is assumed.
    """
    filename = args['<filename>']
    format = args['--format']
    _cr_lib_init(args)
    with open(filename) as f:
        for line in f:
            parts = line.split()
            ds_id = parts[0]
            if len(parts) == 1:
                versions = ['master__tip']
            else:
                versions = parts[1:]
            for version in versions:
                print('{}@{}:'.format(ds_id, version), end=' ')
                sys.stdout.flush()
                try:
                    ds = Dataset.find_by_id(id=ds_id, version=version)
                    info = ds.diagnose()
                    _check_ds_diagnosis(info, format)
                    print('OK')
                except Exception as err:
                    print(err)
                finally:
                    sys.stdout.flush()


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


def do_list_actions(args):
    """
    List all actions for a dataset in chronological order
    """
    ds_id = args['<ds-id>']
    from_version = args['<ds-version>']
    only_successful = not args['--include-failed']
    _cr_lib_init(args)
    try:
        ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    except exceptions.NotFound:
        print("Dataset {} not found.".format(ds_id))
        return 1
    _, history = _get_vtag_actions_list(ds, from_version,
                                        only_successful=only_successful)
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
    for i, action in enumerate(history):
        sys.stdout.write(str(i) + ':\n')
        if args['--long']:
            _print_action(action)
        else:
            pprint.pprint(_abbreviate_action(action))


def _print_action(action):
    write = sys.stdout.write
    write('{\n')
    for k, v in six.iteritems(action):
        if k == 'params':
            write('    "params":\n')
            for k, p in six.iteritems(v):
                write('        "{!s}": {!r}\n'.format(k, p))
        else:
            write('    "{!s}": {!r}\n'.format(k, v))
    write('}\n')


def _abbreviate_action(action):
    d = {}
    for key in ('key', 'utc', 'hash'):
        if key in action:
            d[key] = action[key]
    params = action['params']
    d['params.dataset.id'] = params['dataset']['id']
    d['params.dataset.branch'] = params['dataset']['branch']
    state = action['state']
    d['state.failed'] = state['failed']
    d['state.completed'] = state['completed']
    d['state.played'] = state['played']
    return d


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


def do_save_all_actions(args):
    ds_id = args['<ds-id>']
    filename = args['<filename>']
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    _save_actions(ds, None, filename)


def _save_actions(ds, from_version, filename):
    if from_version is not None:
        from_branch = Dataset.version_branch(from_version)
        if from_branch != ds.branch:
            raise ValueError(
                'Start and End versions must be on same branch.')
    with actionslib.dataset_lock('save_actions', ds.id,
                                 dataset_branch=ds.branch,
                                 exclusive=False):
        _, actions_to_save = _get_vtag_actions_list(ds, from_version)
    print("Saving", len(actions_to_save), "actions to", filename)
    with open(filename, 'wb') as f:
        pickle.dump(actions_to_save, f, 2)


def do_apply_actions(args):
    """Replay some or all of the actions saved in a pickle file."""
    ds_id = args['<ds-id>']
    filename = args['<filename>']
    with open(filename, 'rb') as f:
        actions_to_replay = pickle.load(f)
    assert isinstance(actions_to_replay, list)
    print("Loaded", len(actions_to_replay), "actions from file.")
    offset = 0
    if args['--offset']:
        offset = int(args['--offset'])
        assert offset >= 0
    print("Skipping", offset, "actions from beginning of file.")
    actions_to_replay = actions_to_replay[offset:]
    if not actions_to_replay:
        print("No actions to replay.")
        return
    log.info("ds.fix apply-actions {} {} --offset={}"
             .format(ds_id, filename, offset))
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    with actionslib.dataset_lock('apply_actions', ds.id,
                                 dataset_branch=ds.branch,
                                 exclusive=True):
        print("Replaying", len(actions_to_replay), "actions")
        # Note: At some point we may need an option to replay with rehash=True
        ds.play_workflow(
            None,
            actions_to_replay,
            autorollback=ds.AutorollbackType.LastAction,
            task=None,
        )


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
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
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
