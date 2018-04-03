"""
Helper script for finding and doing stuff with broken datasets

Usage:
    ds.fix [options] actions-vs-s3
    ds.fix [options] migrate-before-tip <ds-id>
    ds.fix [options] info-repo <ds-id>
    ds.fix [options] info-repo-list <filename>
    ds.fix [options] copy-repo <ds-id>

Options:
    -c FILENAME     [default: config.yaml]
    -p PROFILE      [default: cantina]
"""
from __future__ import print_function
import os
import sys
import tempfile
import time

import docopt
import lz4.frame
import yaml


def _directory_is_writable(dirpath):
    try:
        with tempfile.TemporaryFile(dir=dirpath):
            return True
    except OSError:
        return False


def _check_config(config):
    assert not _directory_is_writable(config['read_only_zz9repo'])
    store_config = config['store_config']
    assert _directory_is_writable(store_config['datadir'])
    assert _directory_is_writable(store_config['repodir'])
    assert _directory_is_writable(store_config['tmpdir'])
    assert store_config['class'] == 'simplefs'
    assert store_config['datadir'] != store_config['repodir']
    assert store_config['datadir'] != store_config['tmpdir']
    assert store_config['repodir'] != store_config['tmpdir']


def do_actions_vs_s3(args, config):
    """
    See if a dataset's data in S3 is more recent that the most recent action
    that could have modified zz9 data.
    """
    print("Here I am")
    raise NotImplementedError()


def do_migrate_before_tip(args, config, ds_id):
    print("Migrating dataset", ds_id)
    raise NotImplementedError()


def _readonly_ds_dir(config, ds_id):
    repo_base = config['read_only_zz9repo']
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


def do_info_dataset(args, config, ds_id):
    """
    Print the info about a dataset by scanning the repository
    """
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


def do_info_dataset_list(args, config, filename):
    with open(filename) as f:
        for line in f:
            ds_id = line.split()[0]
            do_info_dataset(args, config, ds_id)
            print()


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


def main():
    t0 = time.time()
    args = docopt.docopt(__doc__)
    with open(args['-c']) as f:
        config = yaml.safe_load(f)[args['-p']]
    _check_config(config)
    try:
        if args["actions-vs-s3"]:
            return do_actions_vs_s3(args, config)
        if args['migrate-before-tip']:
            return do_migrate_before_tip(args, config, args['<ds-id>'])
        if args['info-repo']:
            return do_info_dataset(args, config, args['<ds-id>'])
        if args['info-repo-list']:
            return do_info_dataset_list(args, config, args['<filename>'])
        print("No command, or command not implemented yet.", file=sys.stderr)
        return 1
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main())
