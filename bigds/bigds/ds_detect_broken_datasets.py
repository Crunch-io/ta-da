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
    --rescan-all            Don't read logs to skip already-seen datasets

Commands:
    list    Save list of all dataset IDs found in repo into <filename>
    detect  Read list of dataset IDs from <filename> and check if they are
            broken.

To pause the detect command (which could take days to run), put a file named
"pause" in the current directory. Remove that file to resume.

Log line formats:
    <ds-id> NO-VERSIONS
    <ds-id> <version> NOFORMAT
    <ds-id> - - FailedDatafilesCopy
    <ds-id> <version> <format>  # Status check in progress
    <ds-id> <version> <format> OK
    <ds-id> <version> <format> FailedVersionCopy
    <ds-id> <version> <format> FailedMigration
    <ds-id> <version> <format> FailedDiagnostic
    <ds-id> <version> <format> Failed<some-other-failure>
A line in any other format is an error detail line (traceback, etc.)
"""
from __future__ import print_function
import datetime
import os
from os.path import join
import multiprocessing.pool
import re
import shutil
import sys
import tempfile
import time
import traceback

import docopt
import lz4.frame
import yaml

import zz9d.stores
import zz9d.objects.datasets
import zz9d.execution

LATEST_FORMAT = '25'


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
            for ds_id in os.listdir(join(ro_repo_base, prefix_name)):
                if not re.match(r'[0-9a-f]{32}', ds_id):
                    print("Skipping extraneous dataset dir:", ds_id,
                          file=sys.stderr)
                    continue
                f.write(ds_id)
                f.write('\n')
                _write('.')
            _write('\n')


def do_detect(args, filename, start_ds_id=None, tip_only=True):
    """
    Detect broken datasets, reading dataset IDs from filename
    """
    config = _load_config(args)
    log_dirname = args['--log-dir']
    if not os.path.isdir(log_dirname):
        os.makedirs(log_dirname)
    log_filename = join(
        log_dirname,
        datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S.%f') + '.log')
    pool = multiprocessing.pool.ThreadPool(3)
    ds_id_list = _read_ds_ids(filename, start_ds_id)
    if args['--rescan-all']:
        _write('Ignoring previous results, rescanning all datasets')
    else:
        _write('Reading logs\n')
        ds_id_status_map = _read_dataset_statuses(args)
        num_before = len(ds_id_list)
        ds_id_list = _filter_finished_datasets(ds_id_list, ds_id_status_map)
        _write('Skipping {} datasets with known statuses\n'.format(
            num_before - len(ds_id_list)))
    try:
        _write('Detecting broken datasets\n')
        with open(log_filename, 'w') as log_f:
            for ds_num, ds_id in enumerate(ds_id_list, 1):
                _check_pause_flag()
                _write("{}/{} {} ".format(ds_num, len(ds_id_list), ds_id))
                _check_dataset(config, pool, log_f, ds_id, tip_only)
                _write('\n')
    finally:
        _write('\nWaiting for ThreadPool cleanup...')
        pool.close()
        pool.join()
        _write('Done.\n')


# Note: This function only works when there is only one status per dataset.
# If we later start checking versions other than master__tip then this needs to
# be revisited.
def _read_dataset_statuses(args):
    """
    Parse the logs to determine the status of dataset checks
    Return: Map of dataset ID to status, any status not "OK" is bad
    """
    log_dir = args['--log-dir']
    ds_id_status_map = {}
    for name in sorted(os.listdir(log_dir)):
        path = join(log_dir, name)
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            for line in f:
                m = re.match(r'[a-f0-d]{15,32}\s', line, re.I)
                if not m:
                    continue
                parts = line.split()
                ds_id = parts[0]
                if ((len(parts) in (2, 3) and parts[-1].startswith('NO'))
                        or len(parts) == 4):
                    ds_id_status_map[ds_id] = parts[-1]
                elif len(parts) == 3:
                    # Still in progress
                    ds_id_status_map[ds_id] = None
    return ds_id_status_map


def _filter_finished_datasets(ds_id_list, ds_id_status_map):
    return [ds_id for ds_id in ds_id_list if not ds_id_status_map.get(ds_id)]


def _read_ds_ids(filename, start_ds_id=None):
    ds_id_list = []
    with open(filename) as ds_id_f:
        for line in ds_id_f:
            ds_id = line.strip()
            if not ds_id:
                continue
            if start_ds_id is not None:
                if ds_id != start_ds_id:
                    continue
                start_ds_id = None
            ds_id_list.append(ds_id)
    return ds_id_list


def _write(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def _check_pause_flag():
    message_emitted = False
    while os.path.exists('pause'):
        if not message_emitted:
            print("Paused at",
                  time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                  file=sys.stderr)
            sys.stderr.flush()
            message_emitted = True
        time.sleep(30)
    if message_emitted:
        print("Un-paused at",
              time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
              file=sys.stderr)
        sys.stderr.flush()


def _check_dataset(config, pool, log_f, ds_id, tip_only=True):
    version_format_map = _get_check_version_format_map(config, log_f, ds_id,
                                                       tip_only=tip_only)
    if not version_format_map:
        return
    version_cp_jobs = _check_copy_dataset(config, pool, log_f, ds_id,
                                          version_format_map)
    for job in version_cp_jobs:
        _check_pause_flag()
        version, version_cp_err = job.get()
        format = version_format_map[version]
        print(ds_id, version, format, file=log_f, end=' ')
        log_f.flush()
        if version_cp_err:
            print('FailedVersionCopy', file=log_f)
            print(version_cp_err, file=log_f)
            log_f.flush()
            _write('!')
            continue
        _check_dataset_version(config, log_f, ds_id, version, format)
    log_f.flush()
    _delete_local_dataset_copy(config, pool, ds_id, list(version_format_map))


def _check_dataset_version(config, log_f, ds_id, version, format):
    branch, revision = version.split('__')
    store = _get_zz9_store(config)
    ds = zz9d.objects.datasets.DatasetVersion(
        ds_id, store, '', branch=branch, revision=revision)
    zz9d.execution.runtime.job.dataset = ds
    if format != LATEST_FORMAT:
        try:
            _write('M')
            ds.migrate()
            format = LATEST_FORMAT  # for correct comparison later
        except Exception:
            print('FailedMigration', file=log_f)
            traceback.print_exc(file=log_f)
            _write('!')
            return
    try:
        _write('D')
        info = ds.diagnose()
        _check_ds_diagnosis(info, format)
    except Exception:
        print('FailedDiagnostic', file=log_f)
        traceback.print_exc(file=log_f)
        _write('!')
        return
    print('OK', file=log_f)
    _write('.')


def _check_ds_diagnosis(info, format):
    # TODO: What else should I look for?
    if info['writeflag']:
        raise Exception("Non-empty writeflag present.")
    if str(info['format']) != str(format):
        raise Exception("Format {} in diagnosis doesn't match format {}"
                        .format(info['format'], format))


def _get_zz9_store(config):
    store_config = config['store_config']
    return zz9d.stores.get_store(store_config)


def _delete_local_dataset_copy(config, pool, ds_id, versions):
    local_repo_dir = _get_local_zz9repo_dir(config, ds_id)
    pool.apply_async(shutil.rmtree, (local_repo_dir,))
    for version in versions:
        local_data_dir = _get_local_zz9data_dir(config, ds_id, version)
        pool.apply_async(shutil.rmtree, (local_data_dir,))


def _check_copy_dataset(config, pool, log_f, ds_id, version_format_map):
    """Return a list of version subdirectory copy jobs to wait for"""
    _write('C')
    datafiles_cp_job = _copy_dataset_datafiles(config, pool, ds_id)
    versions = list(version_format_map)
    version_cp_jobs = _copy_dataset_versions(config, pool, ds_id, versions)
    # datafiles dir must be completely copied before we migrate any versions
    datafiles_cp_err = None
    if datafiles_cp_job is not None:
        _, datafiles_cp_err = datafiles_cp_job.get()
    if datafiles_cp_err:
        print(ds_id, '-', '-', 'FailedDatafilesCopy', file=log_f)
        print(datafiles_cp_err, file=log_f)
        _write('!')
        # If there was an error copying the datafiles subdirectory,
        # wait for all the copy jobs but don't try to migrate/diagnose.
        for job in version_cp_jobs:
            version, version_cp_err = job.get()
            format = version_format_map[version]
            if version_cp_err:
                # Log the version copy error as well
                print(ds_id, version, format, 'FailedVersionCopy', file=log_f)
                print(version_cp_err, file=log_f)
        log_f.flush()
        return []
    return version_cp_jobs


def _get_check_version_format_map(config, log_f, ds_id, tip_only=True):
    _write('V')
    version_format_map = _get_version_format_map(config, ds_id, tip_only)
    if not version_format_map:
        print(ds_id, 'NO-VERSIONS', file=log_f)
        log_f.flush()
        _write('!')
    for version in list(version_format_map):
        _write('F')
        if not version_format_map[version]:
            del version_format_map[version]
            print(ds_id, version, 'NOFORMAT', file=log_f)
            log_f.flush()
            _write('!')
    return version_format_map


def _copy_dataset_datafiles(config, pool, ds_id):
    """Asynchronously copy datafiles subdir if it exists"""
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    local_repo_dir = _get_local_zz9repo_dir(config, ds_id)
    datafiles_src = join(ro_repo_dir, 'datafiles')
    datafiles_dst = join(local_repo_dir, 'datafiles')
    if os.path.exists(datafiles_src):
        return pool.apply_async(_copy_dir, (datafiles_src, datafiles_dst))
    return None


def _copy_dataset_versions(config, pool, ds_id, versions):
    """Asynchronously copy dataset version subdirectories"""
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    local_repo_dir = _get_local_zz9repo_dir(config, ds_id)
    jobs = []
    for version in versions:
        version_src = join(ro_repo_dir, 'versions', version)
        version_dst = join(local_repo_dir, 'versions', version)
        jobs.append(pool.apply_async(_copy_dir, (version_src, version_dst,
                                                 version)))
    return jobs


def _copy_dir(src, dst, job_id=None):
    result = None
    try:
        copytree(src, dst)
    except Exception as result:
        pass
    return job_id, result


# Copied from shutil and modified to stop on the first error instead of
# accumulating a huge load of errors. shutil.copytree() resulted in an 11MB
# exception message during a disk full situation, which is unproductive.
def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    os.makedirs(dst)
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if symlinks and os.path.islink(srcname):
            linkto = os.readlink(srcname)
            os.symlink(linkto, dstname)
        elif os.path.isdir(srcname):
            copytree(srcname, dstname, symlinks, ignore)
        else:
            # Will raise a SpecialFileError for unsupported file types
            shutil.copy2(srcname, dstname)
    shutil.copystat(src, dst)


def _get_version_format_map(config, ds_id, tip_only=True):
    """Get format of each version of interest"""
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    all_versions = os.listdir(join(ro_repo_dir, 'versions'))
    version_format_map = {}
    for version in all_versions:
        if tip_only and version != 'master__tip':
            continue
        format = _get_dataset_format(config, ds_id, version)
        version_format_map[version] = format
    return version_format_map


def _get_dataset_format(config, ds_id, version):
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    path = join(ro_repo_dir, 'versions', version)
    for format_name in ('format', 'version'):
        try:
            return _read_maybe_lz4_compressed("%s/%s.zz9" % (path, format_name))
        except IOError:
            continue
    return None


def _read_maybe_lz4_compressed(path):
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    with lz4.frame.open(path + '.lz4', mode='r') as f:
        return f.read()


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
    return join(repo_base, prefix, ds_id)


def _get_local_zz9repo_dir(config, ds_id):
    repo_base = config['store_config']['repodir']
    prefix = ds_id[:2]
    return join(repo_base, prefix, ds_id)


def _get_local_zz9data_dir(config, ds_id, version):
    data_dir = config['store_config']['datadir']
    return join(data_dir, '{}@{}'.format(ds_id, version))


def _do_command(args):
    t0 = time.time()
    try:
        if args['list']:
            return do_list(args, args['<filename>'])
        if args['detect']:
            return do_detect(args, args['<filename>'],
                             start_ds_id=args['--start-at'])
        print("No command, or command not implemented yet.", file=sys.stderr)
        return 1
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


def main():
    args = docopt.docopt(__doc__)
    return _do_command(args)


if __name__ == '__main__':
    sys.exit(main())
