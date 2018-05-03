"""
Broken dataset detector script
See: https://www.pivotaltracker.com/story/show/157122927

Usage:
    ds.detect-broken-datasets [options] list <filename>
    ds.detect-broken-datasets [options] detect <filename>...
    ds.detect-broken-datasets [options] summary_report
    ds.detect-broken-datasets [options] ds_ids_report

Options:
    --config=FILENAME       [default: config.yaml]
    --profile=PROFILE       [default: shared-dev]
    --log-dir=DIRNAME       [default: log]
    --rescan-all            Don't read logs to skip already-seen datasets
    --format=FORMAT         Report processed DS IDs with FORMAT
    --status=STATUS         Report processed DS IDs with STATUS

Commands:
    list    Save list of all dataset IDs found in repo into <filename>
    detect  Read dataset IDs from each filename; do migration and diagostic
            tests on each dataset. Rename each file to x.in-progress while it is
            being processed, and x.done when it is done.

To pause the detect command (which could take days to run), put a file named
"pause" in the current directory. Remove that file to resume.

Log line formats:
    <ds-id> NO-VERSIONS
    <ds-id> <version> NOFORMAT
    <ds-id> - - FailedDatafilesCopy
    <ds-id> <version> <format>  # Status check in progress
    <ds-id> <version> <format> OK
    <ds-id> <version> <format> Failed<failure-type>
A line in any other format is an error detail line (traceback, etc.)
"""
from __future__ import print_function
from collections import defaultdict
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
import six
import yaml

import zz9d.stores
import zz9d.objects.datasets
import zz9d.execution

LATEST_FORMAT = '25'

DS_ID_PATTERN = r'[0-9a-f]{15,32}'


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
                if not re.match(DS_ID_PATTERN + '$', ds_id):
                    print("Skipping extraneous dataset dir:", ds_id,
                          file=sys.stderr)
                    continue
                f.write(ds_id)
                f.write('\n')
                _write('.')
            _write('\n')


def do_detect(args, filenames, tip_only=True):
    """Detect broken datasets, reading dataset IDs from filenames"""
    config = _load_config(args)
    log_dirname = args['--log-dir']
    if not os.path.isdir(log_dirname):
        os.makedirs(log_dirname)
    log_filename = join(
        log_dirname,
        datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S.%f') + '.log')
    if args['--rescan-all']:
        _write('Ignoring previous results, rescanning all datasets\n')
        ds_id_status_map = None
    else:
        _write('Reading previous logs\n')
        ds_id_status_map = _read_dataset_statuses(args)
    pool = multiprocessing.pool.ThreadPool(3)
    try:
        _write("Output log: {}\n".format(log_filename))
        with open(log_filename, 'w') as log_f:
            _check_datasets(config, pool, log_f, ds_id_status_map, filenames,
                            tip_only=tip_only)
    finally:
        _write('\nWaiting for ThreadPool cleanup...')
        pool.close()
        pool.join()
        _write('Done.\n')


def do_summary_report(args):
    #                       formats
    # status                -     21    22    23    24    25    all
    # --------------------  ----- ----- ----- ----- ----- ----- -----
    # FailedDataFilesCopy
    # Failed...
    # NO-VERSIONS
    # NOFORMAT
    # None
    # all
    ds_id_status_map = _read_dataset_statuses(args)
    format_set = set(['all'])
    status_set = set(['all'])
    report_table = defaultdict(int)  # { (format, status): count }
    for info in six.itervalues(ds_id_status_map):
        format = str(info['format'])
        status = str(info['status'])
        format_set.add(format)
        status_set.add(status)
        report_table[(format, status)] += 1
        report_table[('all', status)] += 1
        report_table[(format, 'all')] += 1
        report_table[('all', 'all')] += 1
    print("Datasets by format and status")
    print("                     formats")
    print("status              ",
          *['{:>5}'.format(i) for i in sorted(format_set)])
    print("--------------------", *(['-----'] * len(format_set)))
    for status in sorted(status_set):
        print('{:20}'.format(status), end=' ')
        for format in sorted(format_set):
            print('{:5}'.format(report_table[(format, status)]), end=' ')
        print()
    print()


def do_ds_ids_report(args):
    format = args['--format']
    status = args['--status']
    print("# Dataset IDs processed so far", file=sys.stderr)
    if format:
        print("# with format:", format, file=sys.stderr)
    if status:
        print("# with status:", status, file=sys.stderr)
    ds_id_status_map = _read_dataset_statuses(args)
    for ds_id, info in six.iteritems(ds_id_status_map):
        if format and str(info['format']) != format:
            continue
        if status and str(info['status']) != status:
            continue
        print(ds_id)


def _check_datasets(config, pool, log_f, ds_id_status_map, filenames,
                    tip_only=True):
    for filename in filenames:
        processing_filename = filename + '.processing.' + str(os.getpid())
        try:
            os.rename(filename, processing_filename)
        except OSError:
            _write("Input file not found, skipping: {}\n".format(filename))
            continue
        ds_id_list = _read_ds_ids(processing_filename)
        _write("Processing {} dataset IDs in file {}\n".format(
            len(ds_id_list), filename))
        if ds_id_status_map:
            assert isinstance(ds_id_status_map, dict)
            num_before = len(ds_id_list)
            ds_id_list = [ds_id for ds_id in ds_id_list
                          if ds_id not in ds_id_status_map]
            _write('Skipping {} datasets with known statuses\n'.format(
                num_before - len(ds_id_list)))
        try:
            for ds_num, ds_id in enumerate(ds_id_list, 1):
                _check_pause_flag()
                _write("{}/{} {} ".format(ds_num, len(ds_id_list),
                                          ds_id))
                _check_dataset(config, pool, log_f, ds_id, tip_only)
                _write('\n')
        except KeyboardInterrupt:
            os.rename(processing_filename, filename)
            raise
        else:
            os.rename(processing_filename, filename + '.done')


# Note: If we later start checking versions other than master__tip then this
# needs to be revisited.
def _read_dataset_statuses(args):
    """
    Parse the logs to determine the status of dataset checks
    Return: { ds_id: {'format': <format>, 'status': <status>} }
    <format> is '-' when not applicable or unknown.
    """
    log_dir = args['--log-dir']
    ds_id_status_map = {}
    for name in sorted(os.listdir(log_dir)):
        path = join(log_dir, name)
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            for line in f:
                m = re.match(DS_ID_PATTERN + r'\s', line)
                if not m:
                    continue
                parts = line.split()
                if len(parts) < 2 or len(parts) > 4:
                    continue
                ds_id = parts[0]
                info = {'format': '-', 'status': None}
                if (len(parts) in (2, 3) and parts[-1].startswith('NO')
                        or len(parts) == 4):
                    info['status'] = parts[-1]
                elif len(parts) == 2:
                    # Probably a malformed line / not a status line
                    continue
                if len(parts) > 2 and not parts[2].startswith('NO'):
                    info['format'] = parts[2]
                ds_id_status_map[ds_id] = info
    return ds_id_status_map


def _read_ds_ids(filename):
    ds_id_list = []
    with open(filename) as ds_id_f:
        for line in ds_id_f:
            ds_id = line.strip()
            if not ds_id:
                continue
            # Filter out bogus dataset IDs that might have crept in
            if not re.match(DS_ID_PATTERN + '$', ds_id):
                continue
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
    versions = sorted(version_format_map)
    if not versions:
        return
    _write('C')
    try:
        if not _check_copy_dataset_datafiles(config, log_f, ds_id):
            return
        for version in versions:
            _check_pause_flag()
            format = version_format_map[version]
            if not _check_copy_dataset_version(config, log_f, ds_id, version,
                                               format):
                continue
            print(ds_id, version, format, file=log_f, end=' ')
            log_f.flush()
            _check_dataset_version(config, log_f, ds_id, version, format)
    finally:
        log_f.flush()
        _delete_local_dataset_copy(config, pool, ds_id, versions)


def _check_dataset_version(config, log_f, ds_id, version, format):
    branch, revision = version.split('__')
    store = _get_zz9_store(config)
    try:
        ds = zz9d.objects.datasets.DatasetVersion(
            ds_id, store, '', branch=branch, revision=revision)
        zz9d.execution.runtime.job.dataset = ds
    except Exception:
        print('FailedDatasetVersion', file=log_f)
        traceback.print_exc(file=log_f)
        _write('X!')
        return
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
    pool.apply_async(shutil.rmtree, (local_repo_dir, {'ignore_errors': True}))
    for version in versions:
        local_data_dir = _get_local_zz9data_dir(config, ds_id, version)
        pool.apply_async(shutil.rmtree,
                         (local_data_dir, {'ignore_errors': True}))


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


def _check_copy_dataset_datafiles(config, log_f, ds_id):
    """
    Copy datafiles subdir of dataset to the local zz9repo, if it exists.
    Return True iff all is well.
    """
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    local_repo_dir = _get_local_zz9repo_dir(config, ds_id)
    datafiles_src = join(ro_repo_dir, 'datafiles')
    datafiles_dst = join(local_repo_dir, 'datafiles')
    if not os.path.exists(datafiles_src):
        return True
    err = _copy_dir(datafiles_src, datafiles_dst)
    if err:
        print(ds_id, '-', '-', 'FailedDatafilesCopy', file=log_f)
        print(err, file=log_f)
        log_f.flush()
        _write('!')
        return False
    return True


def _check_copy_dataset_version(config, log_f, ds_id, version, format):
    """
    Copy a dataset version directory to the local zz9repo.
    Return True iff all is well.
    """
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    local_repo_dir = _get_local_zz9repo_dir(config, ds_id)
    version_src = join(ro_repo_dir, 'versions', version)
    version_dst = join(local_repo_dir, 'versions', version)
    err = _copy_dir(version_src, version_dst)
    if err:
        print(ds_id, version, format, 'FailedVersionCopy', file=log_f)
        print(version_cp_err, file=log_f)
        log_f.flush()
        _write('!')
        return False
    return True


def _copy_dir(src, dst):
    """
    Attempt to copy a directory tree.
    Return the Exception object, or None if there was no error.
    """
    try:
        copytree(src, dst)
    except Exception as result:
        return result
    else:
        return None


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
    try:
        all_versions = os.listdir(join(ro_repo_dir, 'versions'))
    except OSError:
        all_versions = []
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
    filenames = args['<filename>']
    assert isinstance(filenames, list)
    try:
        if args['list']:
            return do_list(args, filenames[0])
        if args['detect']:
            return do_detect(args, filenames)
        if args['summary_report']:
            return do_summary_report(args)
        if args['ds_ids_report']:
            return do_ds_ids_report(args)
        print("No command, or command not implemented yet.", file=sys.stderr)
        return 1
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


def main():
    args = docopt.docopt(__doc__)
    return _do_command(args)


if __name__ == '__main__':
    sys.exit(main())
