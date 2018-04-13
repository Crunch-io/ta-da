"""
Helper script for finding and doing stuff with broken datasets

Usage:
    ds.fix [options] info-repo <ds-id>
    ds.fix [options] copy-repo <ds-id>
    ds.fix [options] look <ds-id> [<ds-version>]
    ds.fix [options] restore-from-savepoint <ds-id> [<ds-version>]

Options:
    -i                      Run interactive prompt after the command
    -w                      Get info from the writable repo, not the readonly
    --cr-lib-config=FILENAME
                            [default: /var/lib/crunch.io/cr.server-0.conf]
    --zz9-config=FILENAME   [default: config.yaml]
    --zz9-profile=PROFILE   [default: shared-dev]

WARNING!!! restore-from-savepoint is currently experimental/dangerous.
"""
from __future__ import print_function
import os
import shutil
import sys
import tempfile
import time

import docopt
import lz4.frame
import yaml

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


def _load_zz9_config(args):
    # Note: This is *not* the same as the zz9 config found in
    # /var/lib/crunch.io -- it is simpler and specific to this tool.
    with open(args['--zz9-config']) as f:
        config = yaml.safe_load(f)[args['--zz9-profile']]
    _check_zz9_config(config)
    return config


def _check_zz9_config(config):
    if 'read_only_zz9repo' in config:
        assert not _directory_is_writable(config['read_only_zz9repo'])
    store_config = config['store_config']
    assert _directory_is_writable(store_config['datadir'])
    assert _directory_is_writable(store_config['repodir'])
    assert _directory_is_writable(store_config['tmpdir'])
    assert store_config['class'] == 'simplefs'
    assert store_config['datadir'] != store_config['repodir']
    assert store_config['datadir'] != store_config['tmpdir']
    assert store_config['repodir'] != store_config['tmpdir']


def _directory_is_writable(dirpath):
    try:
        with tempfile.TemporaryFile(dir=dirpath):
            return True
    except OSError:
        return False


def _readonly_ds_dir(config, ds_id):
    repo_base = config['read_only_zz9repo']
    prefix = ds_id[:2]
    return os.path.join(repo_base, prefix, ds_id)


def _writable_ds_dir(config, ds_id):
    repo_base = config['store_config']['repodir']
    prefix = ds_id[:2]
    return os.path.join(repo_base, prefix, ds_id)


def _calc_ds_summary(ds_info):
    total_filesize = 0
    num_files = len(ds_info.get('stray_files', []))
    num_dirs = len(ds_info.get('stray_subdirs', []))
    ds_formats = set()
    for subdir_map in (ds_info['data_dirs'], ds_info['version_dirs']):
        for info in subdir_map.values():
            total_filesize += info['total_filesize']
            num_files += info['num_files']
            num_dirs += info['num_dirs']
            if info['ds_format']:
                ds_formats.add(info['ds_format'])
    return {
        'total_filesize': total_filesize,
        'num_files': num_files,
        'num_dirs': num_dirs,
        'ds_formats': ds_formats,
    }


def do_info_dataset(args, ds_id):
    """
    Print the info about a dataset by scanning the repository
    """
    config = _load_zz9_config(args)
    if args['-w']:
        ds_dir = _writable_ds_dir(config, ds_id)
    else:
        ds_dir = _readonly_ds_dir(config, ds_id)
    if not os.path.isdir(ds_dir):
        print("Dataset directory does not exist:", ds_dir, file=sys.stderr)
        return 1
    ds_info = get_dataset_info(ds_dir)
    ds_summary = _calc_ds_summary(ds_info)
    print()
    print(" Total filesize:", ds_summary['total_filesize'])
    print(" Num subdirs   :", ds_summary['num_dirs'])
    print(" Num files     :", ds_summary['num_files'])
    print(" Formats       :", ds_summary['ds_formats'])


def get_dataset_info(ds_dir):
    print("Dataset directory:", ds_dir)
    stray_files = []
    stray_subdirs = []
    data_dirs = {}
    version_dirs = {}
    for name in os.listdir(ds_dir):
        subdir = os.path.join(ds_dir, name)
        if not os.path.isdir(subdir):
            print("  Stray file:", name)
            stray_files.append(name)
            continue
        if not name in ('datafiles', 'versions'):
            print("  Stray sub-directory:", name)
            stray_subdirs.append(name)
            continue
        print("  {}:".format(name))
        for subname in os.listdir(subdir):
            subsubdir = os.path.join(subdir, subname)
            print("    {}:".format(subname))
            info = get_dataset_subdir_info(subsubdir)
            if name == 'datafiles':
                data_dirs[subname] = info
            else:
                version_dirs[subname] = info
            print("      Total filesize:", info['total_filesize'])
            print("      Num subdirs   :", info['num_dirs'])
            print("      Num files     :", info['num_files'])
            print("      Format        :", info['ds_format'])
    return {
        'ds_dir': ds_dir,
        'stray_files': stray_files,
        'stray_subdirs': stray_subdirs,
        'data_dirs': data_dirs,
        'version_dirs': version_dirs,
    }


def get_dataset_subdir_info(ds_version_dir):
    """
    Return dictionary of info about a dataset version or data sub-directory
    """
    total_filesize = 0
    num_files = 0
    num_dirs = 0
    ds_format = None
    if os.path.isfile(ds_version_dir):
        total_filesize = os.path.getsize(ds_version_dir)
        num_files = 1
    else:
        for dirpath, dirnames, filenames in os.walk(ds_version_dir):
            num_dirs += len(dirnames)
            num_files += len(filenames)
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_filesize += os.path.getsize(filepath)
                if filename == 'format.zz9':
                    with open(filepath) as f:
                        ds_format = f.read()
                elif filename == 'format.zz9.lz4':
                    with lz4.frame.open(filepath, mode='r') as f:
                        ds_format = f.read()
    return {
        'total_filesize': total_filesize,
        'num_files': num_files,
        'num_dirs': num_dirs,
        'ds_format': ds_format,
    }


def do_copy_dataset(args, ds_id):
    """
    Copy a dataset from the read-only repository to the writable local one.
    """
    config = _load_zz9_config(args)
    ro_ds_dir = _readonly_ds_dir(config, ds_id)
    wr_ds_dir = _writable_ds_dir(config, ds_id)
    if os.path.exists(wr_ds_dir):
        print('Destination directory "{}" already exists'.format(wr_ds_dir),
              file=sys.stderr)
        return 1
    print('Copying "{}" to "{}"'.format(ro_ds_dir, wr_ds_dir))
    shutil.copytree(ro_ds_dir, wr_ds_dir)


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
        if args['info-repo']:
            return do_info_dataset(args, args['<ds-id>'])
        if args['copy-repo']:
            return do_copy_dataset(args, args['<ds-id>'])
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
