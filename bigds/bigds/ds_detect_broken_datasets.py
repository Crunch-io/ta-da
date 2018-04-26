"""
Broken dataset detector script
See: https://www.pivotaltracker.com/story/show/157122927

Usage:
    ds.detect-broken-datasets [options] list <filename>
    ds.detect-broken-datasets [options] detect <filename>

Options:
    --config=FILENAME       [default: config.yaml]
    --profile=PROFILE       [default: shared-dev]
    --start-at=DSID         Start detection at dataset DSID
    --log-dir=DIRNAME       [default: log]

Commands:
    list    Save list of all dataset IDs found in repo into <filename>
    detect  Read list of dataset IDs from <filename> and check if they are
            broken.

To pause the detect command (which could take days to run), put a file named
"pause" in the current directory. Remove that file to resume.
"""
from __future__ import print_function
import glob
import os
import re
import shutil
import sys
import tempfile
import time

import docopt
import lz4.frame
import yaml


def do_list(args, filename):
    """
    List dataset IDs, saving them in filename.
    Datasets are discovered by looking in the read-only repo directory.
    """
    # I don't call os.path.isdir() on purpose because EFS is
    # so slow. I rely on directory naming conventions instead.
    config = _load_config(args)
    ro_repo_base = _get_readonly_zz9repo_base(config)
    with open(filename, 'w') as f:
        for prefix_name in os.listdir(ro_repo_base):
            if len(prefix_name) != 2:
                print("Skipping extraneous prefix dir:", prefix_name,
                      file=sys.stderr)
                continue
            for ds_id in os.listdir(os.path.join(ro_repo_base, prefix_name)):
                if not re.match(r'[0-9a-f]{32}', ds_id):
                    print("Skipping extraneous dataset dir:", ds_id,
                          file=sys.stderr)
                    continue
                f.write(ds_id)
                f.write('\n')
                sys.stdout.write('.')
                sys.stdout.flush()
            sys.stdout.write('\n')
            sys.stdout.flush()


def do_detect(args, filename):
    """
    Detect broken datasets, reading dataset IDs from filename
    """
    config = _load_config(args)
    log_dirname = args['--log-dir']
    if not os.path.isdir(log_dirname):
        os.makedirs(log_dirname)
    with open(filename) as f:
        for line in f:
            ds_id = line.strip()
            if not ds_id:
                continue
            _check_pause_flag()
            _check_dataset(config, None, ds_id)


def _check_pause_flag():
    message_emitted = False
    while os.path.exists('pause'):
        if not message_emitted:
            print("Paused at", time.strftime('%Y-%m-%d %H:%M:%S UTC',
                                             time.gmtime()))
            sys.stdout.flush()
            message_emitted = True
        time.sleep(30)
    if message_emitted:
        print("Un-paused at", time.strftime('%Y-%m-%d %H:%M:%S UTC',
                                            time.gmtime()))
        sys.stdout.flush()


def _check_dataset(config, log_f, ds_id):
    """
    Return:
        True if the dataset exists and is Ok
        False if the dataset does not exist or has problems
    """
    try:
        pass
    except Exception as err:
        sys.stdout.write('E')
    else:
        sys.stdout.write('.')
    sys.stdout.flush()


def _load_config(args):
    # Note: This is *not* the same as the zz9 config found in
    # /var/lib/crunch.io -- it is simpler and specific to this tool.
    with open(args['--config']) as f:
        config = yaml.safe_load(f)[args['--profile']]
    _check_config(config)
    return config


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


def _directory_is_writable(dirpath):
    try:
        with tempfile.TemporaryFile(dir=dirpath):
            return True
    except OSError:
        return False


def _get_readonly_zz9repo_base(config):
    return config['read_only_zz9repo']


def _get_readonly_zz9repo_dir(config, ds_id):
    repo_base = _get_readonly_zz9repo_base(config)
    prefix = ds_id[:2]
    return os.path.join(repo_base, prefix, ds_id)


def _get_writable_zz9repo_dir(config, ds_id):
    repo_base = config['store_config']['repodir']
    prefix = ds_id[:2]
    return os.path.join(repo_base, prefix, ds_id)


def _do_command(args):
    t0 = time.time()
    try:
        if args['list']:
            return do_list(args, args['<filename>'])
        if args['detect']:
            return do_detect(args, args['<filename>'])
        print("No command, or command not implemented yet.", file=sys.stderr)
        return 1
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


def main():
    args = docopt.docopt(__doc__)
    return _do_command(args)


if __name__ == '__main__':
    sys.exit(main())
