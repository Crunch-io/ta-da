"""
Helper script for finding and doing stuff with broken datasets

Usage:
    ds.fix [options] list-versions <ds-id>
    ds.fix [options] list-all-actions [--long] <ds-id>
    ds.fix [options] save-actions <ds-id> <ds-version> <filename>
    ds.fix [options] show-actions [--long] <filename>
    ds.fix [options] revert-to-version <ds-id> <ds-version>
    ds.fix [options] replay-actions <ds-id> <filename>

Options:
    -i                      Run interactive prompt after the command
    --cr-lib-config=FILENAME
                            [default: /var/lib/crunch.io/cr.server-0.conf]

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
from cr.lib.entities.actions import Action
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib.entities.datasets.versions.versioning import (
    version_health,
    VersionTag,
)
import cr.lib.index.indexer
from cr.lib.settings import settings
from zz9lib import frame as framelib

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
    for version_info in version_list:
        pprint.pprint(version_info)
    return {
        'ds_id': ds_id,
        'version_list': version_list,
    }


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
            pprint.pprint(actions)
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


def do_revert_to_version(args):
    ds_id = args['<ds-id>']
    ds_version = args['<ds-version>']
    _cr_lib_init(args)
    ds = Dataset.find_by_id(id=ds_id, version='master__tip')
    svp = VersionTag.find_one(dict(dataset_id=ds_id, version=ds_version))
    if not svp:
        raise ValueError("Couldn't find savepoint for "
                         "ds_id={} branch={} revision={}"
                         .format(ds_id, ds.branch, ds.revision))
    ds.drop_versions(['master__tip'])
    framelib.ZZ9Dataset.create(ds)
    ds.restore_savepoint(svp)
    push_result = ds.query(dict(command='release', push=True))
    return {
        'ds_id': ds_id,
        'ds_version': ds_version,
        'ds': ds,
        'push_result': push_result,
        'svp': svp,
    }


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
