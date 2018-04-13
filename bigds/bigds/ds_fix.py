"""
Helper script for finding and doing stuff with broken datasets

Usage:
    ds.fix [options] look <ds-id> [<ds-version>]
    ds.fix [options] restore-from-savepoint <ds-id> [<ds-version>]

Options:
    -i                      Run interactive prompt after the command
    --cr-lib-config=FILENAME
                            [default: /var/lib/crunch.io/cr.server-0.conf]

WARNING!!! restore-from-savepoint is currently experimental/dangerous.
"""
from __future__ import print_function
import sys
import time

import docopt

from cr.lib.commands.common import load_settings, startup
import cr.lib.entities.datasets.dataset
import cr.lib.index.indexer
from cr.lib.settings import settings


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args['--cr-lib-config']
    settings.update(load_settings(settings_yaml))
    startup()


def do_look(args, ds_id, ds_version=None):
    """This command is not useful without the -i option"""
    _cr_lib_init(args)
    if not ds_version:
        ds_version = 'master__tip'
    ds = cr.lib.entities.datasets.dataset.Dataset.find_by_id(id=ds_id,
                                                             version=ds_version)
    return {
        'ds_id': ds_id,
        'ds_version': ds_version,
        'ds': ds,
    }


def do_restore_from_savepoint(args, ds_id, ds_version=None):
    _cr_lib_init(args)
    if not ds_version:
        ds_version = 'master__tip'
    ds = cr.lib.entities.datasets.dataset.Dataset.find_by_id(id=ds_id,
                                                             version=ds_version)
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
        if args['look']:
            return do_look(args, args['<ds-id>'], args['<ds-version>'])
        if args['restore-from-savepoint']:
            return do_restore_from_savepoint(args, args['<ds-id>'],
                                             args['<ds-version>'])
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
