"""
Broken dataset detector script
See: https://www.pivotaltracker.com/story/show/157122927

Usage:
    ds.detect-broken-datasets [options] list <filename>
    ds.detect-broken-datasets [options] detect <filename>...
    ds.detect-broken-datasets [options] summary_report [<filename>]
    ds.detect-broken-datasets [options] ds_ids_report
    ds.detect-broken-datasets [options] ds_details_report
    ds.detect-broken-datasets [options] cleanup-local-zz9repo <ds-id>
    ds.detect-broken-datasets [options] clean-logs

Options:
    --config=FILENAME       [default: config.yaml]
    --profile=PROFILE       [default: shared-dev]
    --log-dir=DIRNAME       [default: log]
    --rescan-all            Don't read logs to skip already-seen datasets
    --format=FORMAT         Report processed DS IDs with FORMAT
    --status=STATUS         Report processed DS IDs with STATUS
    --skip-cleanup          Don't delete local dataset copies afterwards
    --skip-latest           Don't look at datasets already at the latest format
    --skip-tip              Skip master__tip when listing dataset versions

Commands:
    list    Save list of all dataset IDs and versions found in repo into
            <filename>. Format is one dataset per line, dataset ID followed by
            space-separated list of versions.
    detect  Read dataset IDs and versions from each filename; do migration and
            diagostic tests on each dataset version. If no version listed for a
            dataset, assume master__tip. Rename each file to x.in-progress while
            it is being processed, and x.done when it is done.

To pause the detect command (which could take days to run), put a file named
"pause" in the current directory. Remove that file to resume.

Log line formats:
    <ds-id> DS-DELETED
    <ds-id> NO-VERSIONS
    <ds-id> <version> NOFORMAT
    <ds-id> - - FailedDatafilesCopy
    <ds-id> <version> <format>  # Status check in progress
    <ds-id> <version> <format> SKIPPED
    <ds-id> <version> <format> OK
    <ds-id> <version> <format> Failed<failure-type>
A line in any other format is an error detail line (traceback, etc.)
"""
from __future__ import print_function
from collections import defaultdict, OrderedDict
import datetime
import glob
import json
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

try:
    import zz9d
except ImportError:
    zz9d = None
else:
    import zz9d.stores
    import zz9d.objects.datasets
    import zz9d.execution

this_module = sys.modules[__name__]

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
                print("Skipping extraneous prefix dir:", prefix_name)
                continue
            for ds_id in os.listdir(join(ro_repo_base, prefix_name)):
                if not re.match(DS_ID_PATTERN + '$', ds_id):
                    print("Skipping extraneous dataset dir:", ds_id)
                    continue
                versions_dir = join(ro_repo_base, prefix_name, ds_id,
                                    'versions')
                try:
                    versions = os.listdir(versions_dir)
                except OSError:
                    print("Skipping dataset because missing versions dir:",
                          ds_id)
                    continue
                if args['--skip-tip']:
                    versions = [v for v in versions if v != 'master__tip']
                if not versions:
                    print("Skipping dataset because it has no versions:", ds_id)
                    continue
                f.write(ds_id)
                for version in versions:
                    f.write(' ')
                    f.write(version)
                f.write('\n')


def do_detect(args, filenames):
    """Detect broken datasets, reading dataset IDs from filenames"""
    config = _load_config(args)
    log_dirname = args['--log-dir']
    if not os.path.isdir(log_dirname):
        os.makedirs(log_dirname)
    if args['--rescan-all']:
        _write('Ignoring previous results, rescanning all datasets\n')
        ds_status_map = None
    else:
        _write('Reading previous logs\n')
        ds_status_map = _read_dataset_statuses(args)
    pool = multiprocessing.pool.ThreadPool(5)
    log_timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S.%f')
    try:
        with tempfile.NamedTemporaryFile(mode='w',
                                         prefix=log_timestamp + '-',
                                         suffix='.log',
                                         dir=log_dirname,
                                         delete=False) as log_f:
            _write("Output log: {}\n".format(log_f.name))
            os.chmod(log_f.name, 0o664)
            dataset_checker = _DatasetChecker(args, config, pool, log_f,
                                              ds_status_map)
            dataset_checker(filenames)
    finally:
        _write('\nWaiting for ThreadPool cleanup...')
        pool.close()
        pool.join()
        _write('Done.\n')


def do_summary_report(args):
    """
    Print a summary report of dataset version statuses.
    If the optional <filename> is given, read dataset IDs/versions from that
    file. Any dataset version in that file that does not appear in the logs has
    its status counted as "NotYetScanned".
    """
    #                       formats
    # status                -     21    22    23    24    25    all
    # --------------------  ----- ----- ----- ----- ----- ----- -----
    # DS-DELETED
    # FailedDataFilesCopy
    # Failed...
    # NO-VERSIONS
    # SKIPPED
    # NOFORMAT
    # None
    # all
    ds_status_map = _read_dataset_statuses(args)
    format_set = set(['all'])
    status_set = set(['all'])
    report_table = defaultdict(int)  # { (format, status): count }
    if args['<filename>']:
        filename = args['<filename>'][0]  # it's a list
        ds_id_versions_list = _read_ds_ids_versions(filename)
        format = '-'
        status = 'NotYetScanned'
        format_set.add(format)
        status_set.add(status)
        for ds_id, versions in ds_id_versions_list:
            for version in versions:
                if (ds_id, version) not in ds_status_map:
                    report_table[(format, status)] += 1
                    report_table[('all', status)] += 1
                    report_table[(format, 'all')] += 1
                    report_table[('all', 'all')] += 1
    for info in six.itervalues(ds_status_map):
        format = str(info['format'])
        status = str(info['status'])
        format_set.add(format)
        status_set.add(status)
        report_table[(format, status)] += 1
        report_table[('all', status)] += 1
        report_table[(format, 'all')] += 1
        report_table[('all', 'all')] += 1
    print("Dataset versions by format and status")
    print("                     formats")
    print("status              ",
          *['{:>6}'.format(i) for i in sorted(format_set)])
    print("--------------------", *(['------'] * len(format_set)))
    for status in sorted(status_set):
        print('{:20}'.format(status), end=' ')
        for format in sorted(format_set):
            print('{:6}'.format(report_table[(format, status)]), end=' ')
        print()
    print()


def do_ds_ids_report(args):
    format = args['--format']
    status = args['--status']
    print("# Dataset versions processed so far", file=sys.stderr)
    if format:
        print("# with format:", format, file=sys.stderr)
    if status:
        print("# with status:", status, file=sys.stderr)
    ds_status_map = _read_dataset_statuses(args)
    ds_id_versions_map = defaultdict(list)
    for (ds_id, version), info in six.iteritems(ds_status_map):
        if format and str(info['format']) != format:
            continue
        if status and str(info['status']) != status:
            continue
        ds_id_versions_map[ds_id].append(version)
    for ds_id, versions in six.iteritems(ds_id_versions_map):
        print(ds_id, ' '.join(sorted(versions)))


def do_ds_details_report(args):
    format = args['--format']
    status = args['--status']
    print("# Dataset test migration results", file=sys.stderr)
    if format:
        print("# with format:", format, file=sys.stderr)
    if status:
        print("# with status:", status, file=sys.stderr)
    ds_result_map = _index_result_logs(args)
    print("# Number of results before filtering:", len(ds_result_map),
          file=sys.stderr)
    f, line_num, line = None, None, None
    num_filtered_results = 0
    try:
        for (ds_id, version), result in six.iteritems(ds_result_map):
            if format and str(result['format']) != format:
                continue
            if status and str(result['status']) != status:
                continue
            num_filtered_results += 1
            if f is None:
                f, line_num, line = open(result['filename'], 'r'), 0, None
            elif f.name != result['filename']:
                f.close()
                f, line_num, line = open(result['filename'], 'r'), 0, None
            while line_num < result['line_start']:
                line = f.readline()
                if line:
                    line_num += 1
                else:
                    raise Exception("Somehow index results got out of sync")
            while True:
                print(line.rstrip())
                if line_num >= result['line_end']:
                    break
                line = f.readline()
                if line:
                    line_num += 1
                else:
                    break
    finally:
        if f is not None:
            f.close()
    print("# Number of filtered results:", num_filtered_results,
          file=sys.stderr)


def do_cleanup_local_zz9repo(args):
    """
    Delete from a local zz9repo directory for a dataset:
        - version sub-directories that have already been processed
        - datafiles sub-directories that have already been processed
    """
    ds_id = args['<ds-id>']
    config = _load_config(args)
    print("Reading dataset/version statuses")
    ds_status_map = _read_dataset_statuses(args)
    local_repo_dir = _get_local_zz9repo_dir(config, ds_id)
    print("Looking at versions of dataset:", ds_id)
    for (cur_ds_id, version), info in six.iteritems(ds_status_map):
        if cur_ds_id != ds_id:
            continue
        status = info['status']
        if not status or status == 'None':
            continue
        # It's an already-processed version
        data_dir = join(local_repo_dir, 'datafiles', version)
        if os.path.exists(data_dir):
            print("Removing data subdir:", data_dir)
            shutil.rmtree(data_dir)
        version_dir = join(local_repo_dir, 'versions', version)
        if os.path.exists(version_dir):
            print("Removing version subdir:", version_dir)
            shutil.rmtree(version_dir)
    print("Done.")


def do_clean_logs(args):
    """
    Delete items from logs that pertain to a given status and/or version.
    If no filter criteria given, don't delete anything.
    """
    format = args['--format']
    status = args['--status']
    if not (format or status):
        print("# Use --format and/or --status to indicate log items to delete.",
              file=sys.stderr)
        return
    print("# Deleting items from logs", file=sys.stderr)
    if format:
        print("# with format:", format, file=sys.stderr)
    if status:
        print("# with status:", status, file=sys.stderr)
    ds_result_map = _index_result_logs(args)
    print("# Number of results before filtering:", len(ds_result_map),
          file=sys.stderr)
    cleaner = _LogCleaner(ds_result_map, format=format, status=status)
    num_deleted_items = cleaner()
    print("# Number of deleted log items:", num_deleted_items,
          file=sys.stderr)


class _LogCleaner(object):

    def __init__(self, ds_result_map, format=None, status=None):
        self.ds_result_map = ds_result_map
        self.format = format
        self.status = status
        #####
        self.filename_suffix = '-filtering.{}'.format(os.getpid())
        self.rf = None
        self.wf = None
        self.line_num = None
        self.changes_in_cur_file = None

    def _ensure_processing_file(self, filename):
        if self.rf is None:
            # Open first file
            if filename:
                self._open_file(filename)
        elif self.rf.name != filename:
            # Changing to a different file or closing last file
            if self.changes_in_cur_file > 0:
                while True:
                    line = self.rf.readline()
                    if not line:
                        break
                    self.wf.write(line)
            self.rf.close()
            self.wf.close()
            if self.changes_in_cur_file > 0:
                os.remove(self.rf.name)
                os.rename(self.wf.name, self.rf.name)
            else:
                os.remove(self.wf.name)
            if filename:
                self._open_file(filename)

    def _open_file(self, filename):
        self.rf = open(filename, 'r')
        self.wf = open(filename + self.filename_suffix, 'w')
        self.line_num = 0
        self.changes_in_cur_file = 0

    def _read_line(self):
        line = self.rf.readline()
        if line:
            self.line_num += 1
        return line

    def __call__(self):
        num_deleted_items = 0
        line = None
        try:
            for (ds_id, version), result in six.iteritems(self.ds_result_map):
                if self.format and str(result['format']) != self.format:
                    continue
                if self.status and str(result['status']) != self.status:
                    continue
                num_deleted_items += 1
                self._ensure_processing_file(result['filename'])
                self.changes_in_cur_file += 1
                while True:
                    line = self._read_line()
                    if not line:
                        raise Exception("Somehow index results got out of sync")
                    if self.line_num >= result['line_start']:
                        break
                    self.wf.write(line)
                while True:
                    print(line.rstrip())
                    if self.line_num >= result['line_end']:
                        break
                    line = self._read_line()
                    if not line:
                        break
        finally:
            self._ensure_processing_file(None)
        return num_deleted_items


class _DatasetChecker(object):

    def __init__(self, args, config, pool, log_f, ds_status_map):
        self.args = args
        self.config = config
        self.pool = pool
        self.log_f = log_f
        self.ds_status_map = ds_status_map

    def __call__(self, filenames):
        for filename in filenames:
            processing_filename = filename + '.processing.' + str(os.getpid())
            try:
                os.rename(filename, processing_filename)
            except OSError:
                _write("Input file not found, skipping: {}\n".format(filename))
                continue
            ds_id_versions_list = _read_ds_ids_versions(processing_filename)
            raw_num_datasets = len(ds_id_versions_list)
            raw_num_versions = _count_versions(ds_id_versions_list)
            _write("Processing {} datasets and {} versions from file {}\n"
                   .format(raw_num_datasets, raw_num_versions, filename))
            if self.ds_status_map:
                ds_id_versions_list = _filter_already_seen_versions(
                    ds_id_versions_list,
                    self.ds_status_map,
                )
                num_datasets = len(ds_id_versions_list)
                num_versions = _count_versions(ds_id_versions_list)
                _write("Filtered {} datasets and {} versions already seen.\n"
                       .format(raw_num_datasets - num_datasets,
                               raw_num_versions - num_versions))
            try:
                for ds_num, (ds_id, versions) in enumerate(ds_id_versions_list,
                                                           1):
                    _check_pause_flag()
                    _write("{}/{} {} ({}):".format(ds_num,
                                                   len(ds_id_versions_list),
                                                   ds_id, len(versions)))
                    self._check_dataset(ds_id, versions)
                    _write('\n')
            except KeyboardInterrupt:
                os.rename(processing_filename, filename)
                raise
            else:
                os.rename(processing_filename, filename + '.done')

    def _log(self, *items, **kwparams):
        end = kwparams.pop('end', None)
        err = kwparams.pop('err', None)
        print_exc = kwparams.pop('print_exc', False)
        print(*items, file=self.log_f, end=end)
        if err:
            print(err, file=self.log_f)
        if print_exc:
            traceback.print_exc(file=self.log_f)
        self.log_f.flush()

    def _check_dataset(self, ds_id, versions):
        version_format_map = self._get_check_version_format_map(ds_id,
                                                                versions)
        if not version_format_map:
            return
        versions = sorted(version_format_map)  # filter versions with no formats
        _write('C')
        local_repo_dir = _get_local_zz9repo_dir(self.config, ds_id)
        try:
            if not self._check_copy_dataset_datafiles(version_format_map,
                                                      ds_id):
                return
            for version in versions:
                _check_pause_flag()
                format = version_format_map[version]
                if not self._check_copy_dataset_version(ds_id, version, format):
                    continue
                self._check_dataset_version(ds_id, version, format)
                if not self.args['--skip-cleanup']:
                    local_data_dir = _get_local_zz9data_dir(self.config,
                                                            ds_id, version)
                    self._async_rmtree(local_data_dir)
                    version_dst = join(local_repo_dir, 'versions', version)
                    self._async_rmtree(version_dst)
                    version_data = join(local_repo_dir, 'datafiles', version)
                    if os.path.exists(version_data):
                        self._async_rmtree(version_data)
        finally:
            if not self.args['--skip-cleanup']:
                self._async_rmtree(local_repo_dir)

    def _async_rmtree(self, dirpath):
        self.pool.apply_async(shutil.rmtree,
                              (dirpath,), {'ignore_errors': True})

    def _get_check_version_format_map(self, ds_id, versions):
        skip_latest_format = self.args['--skip-latest']
        _write('V')
        version_format_map = _get_version_format_map(self.config, ds_id,
                                                     versions)
        if version_format_map is None:
            self._log(ds_id, 'DS-DELETED')
            _write('!')
            return None
        if not version_format_map:
            self._log(ds_id, 'NO-VERSIONS')
            _write('!')
            return {}
        for version in versions:
            _write('F')
            format = version_format_map.get(version)
            if not format:
                version_format_map.pop(version, None)
                self._log(ds_id, version, 'NOFORMAT')
                _write('!')
            elif skip_latest_format and format == LATEST_FORMAT:
                del version_format_map[version]
                self._log(ds_id, version, format, 'SKIPPED')
                _write('S')
        return version_format_map

    def _check_copy_dataset_datafiles(self, version_format_map, ds_id):
        """
        Only copy these things from the datafiles directory:
            - Any *.zz9 or *.zz9.lz4 files directly in the datafiles dir
            - All sub-directories mentioned in the datamap files for the
              versions of interest.
            - Any sub-directories named after a version of interest, that
              wasn't already copied due to datamap files.
        """
        ro_repo_dir = _get_readonly_zz9repo_dir(self.config, ds_id)
        datafiles_src = join(ro_repo_dir, 'datafiles')
        if not os.path.exists(datafiles_src):
            # No datafiles dir in older formats
            return True
        local_repo_dir = _get_local_zz9repo_dir(self.config, ds_id)
        datafiles_dst = join(local_repo_dir, 'datafiles')
        if not os.path.exists(datafiles_dst):
            os.makedirs(datafiles_dst)

        datafiles_items = set(os.listdir(datafiles_src))
        for filename in list(datafiles_items):
            if not (filename.endswith('.zz9') or filename.endswith('.zz9.lz4')):
                continue
            src = join(datafiles_src, filename)
            dst = join(datafiles_dst, filename)
            try:
                shutil.copy(src, dst)
            except (IOError, OSError) as err:
                self._log(ds_id, '-', '-', 'FailedDatafilesCopy', err=err)
                return False
            else:
                datafiles_items.discard(filename)

        if not self._check_copy_filtered_datafiles(version_format_map, ds_id,
                                                   datafiles_items):
            return False

        for version in sorted(version_format_map):
            if version not in datafiles_items:
                continue
            src_dir = join(datafiles_src, version)
            dst_dir = join(datafiles_dst, version)
            err = _copy_dir(src_dir, dst_dir)
            if err:
                format = version_format_map.get(version, '-')
                self._log(ds_id, version, format, 'FailedDatafilesCopy',
                          err=err)
                return False
            datafiles_items.discard(version)
        return True

    def _check_copy_filtered_datafiles(self, version_format_map, ds_id,
                                       datafiles_items):
        """
        Copy the portions of the datafiles of a dataset to the local zz9repo
        that are relevant to the versions in version_format_map, using the
        datamap for each version.
        datafiles_items: A set of items in the source datafiles directory which
        haven't been copied yet. Discard from this as you copy.
        Return True iff all is well.
        """
        ro_repo_dir = _get_readonly_zz9repo_dir(self.config, ds_id)
        datafiles_src = join(ro_repo_dir, 'datafiles')
        local_repo_dir = _get_local_zz9repo_dir(self.config, ds_id)
        datafiles_dst = join(local_repo_dir, 'datafiles')
        data_subdirs = set()
        for version in sorted(version_format_map):
            format = version_format_map[version]
            datamap = self._load_datamap(ds_id, version, format=format)
            if datamap is False:
                # No datamap file - skip this version
                continue
            if datamap is None:
                # Error has already been logged
                return False
            data_subdirs.update([str(v) for v in datamap.values()])
        for data_subdir in sorted(data_subdirs):
            if data_subdir not in datafiles_items:
                # Don't copy items that don't exist or have already been copied.
                continue
            src_dir = join(datafiles_src, data_subdir)
            dst_dir = join(datafiles_dst, data_subdir)
            err = _copy_dir(src_dir, dst_dir)
            if err:
                self._log(ds_id, '-', '-', 'FailedDatafilesCopy', err=err)
                _write('!')
                return False
            datafiles_items.discard(data_subdir)
        return True

    def _load_datamap(self, ds_id, version, format='-'):
        """
        Load the datamap for a dataset version.
        Return False if the datamap doesn't exist (Ok depending on format),
        None if there was an error reading or parsing the datamap,
        else return the datamap dictionary.
        """
        datamap_path = _get_datamap_path(self.config, ds_id, version)
        if not (os.path.exists(datamap_path)
                or os.path.exists(datamap_path + '.lz4')):
            return False
        try:
            datamap_bytes = _read_maybe_lz4_compressed(datamap_path)
        except IOError as err:
            self._log(ds_id, version, format, 'FailedReadingDatamap', err=err)
            _write('!')
            return None
        try:
            datamap = json.loads(datamap_bytes)
        except ValueError as err:
            self._log(ds_id, version, format, 'FailedCorruptDatamap', err=err)
            _write('!')
            return None
        return datamap

    def _check_copy_dataset_version(self, ds_id, version, format):
        """
        Copy a dataset version directory to the local zz9repo.
        Return True iff all is well.
        """
        ro_repo_dir = _get_readonly_zz9repo_dir(self.config, ds_id)
        local_repo_dir = _get_local_zz9repo_dir(self.config, ds_id)
        local_versions_dir = join(local_repo_dir, 'versions')
        if not os.path.exists(local_versions_dir):
            os.makedirs(local_versions_dir)
        version_src = join(ro_repo_dir, 'versions', version)
        version_dst = join(local_versions_dir, version)
        err = _copy_dir(version_src, version_dst)
        if err:
            self._log(ds_id, version, format, 'FailedVersionCopy', err=err)
            _write('!')
            return False
        return True

    def _check_dataset_version(self, ds_id, version, format):
        self._log(ds_id, version, format, end=' ')
        store = _get_zz9_store(self.config)
        try:
            ds = zz9d.objects.datasets.DatasetNode(ds_id, version, store, None)
            zz9d.execution.runtime.job.dataset = ds
        except Exception:
            self._log('FailedDatasetNode', print_exc=True)
            _write('X!')
            return
        if format != LATEST_FORMAT:
            try:
                _write('M')
                ds.migrate()
                format = LATEST_FORMAT  # for correct comparison later
            except Exception:
                self._log('FailedMigration', print_exc=True)
                _write('!')
                return
        try:
            _write('D')
            info = ds.diagnose()
            _check_ds_diagnosis(info, format)
        except Exception:
            self._log('FailedDiagnostic', print_exc=True)
            _write('!')
            return
        self._log('OK')
        _write('.')


def _count_versions(ds_id_versions_list):
    return sum(len(i[1]) for i in ds_id_versions_list)


def _filter_already_seen_versions(ds_id_versions_list, ds_status_map):
    filtered_ds_id_versions_list = []
    for ds_id, versions in ds_id_versions_list:
        filtered_versions = []
        for version in versions:
            if (ds_id, version) in ds_status_map:
                continue
            filtered_versions.append(version)
        if filtered_versions:
            filtered_ds_id_versions_list.append((ds_id, filtered_versions))
    return filtered_ds_id_versions_list


def _analyze_log_line(line):
    """
    If the line is a dataset migration summary line, return:
        {
            'ds_id': <dataset-ID>,
            'version': version,
            'format': format,
            'status': status,
        }
    Else return None.
    version and format are '-' when not applicable or unknown.
    status is None if no status reported yet.
    """
    m = re.match(DS_ID_PATTERN + r'\s', line)
    if not m:
        return None
    parts = line.split()
    if len(parts) < 2 or len(parts) > 4:
        return None
    ds_id = parts[0]
    version = '-'
    format = '-'
    status = None
    if len(parts) == 2:
        status = parts[-1]
    elif len(parts) == 3:
        version = parts[1]
        try:
            int(parts[2])
        except ValueError:
            # Not an integer, so must be a status
            status = parts[2]
        else:
            format = parts[2]  # keep format as a string
    else:
        version = parts[1]
        format = parts[2]
        status = parts[3]
    return {
        'ds_id': ds_id,
        'version': version,
        'format': format,
        'status': status,
    }


def _read_dataset_statuses(args):
    """
    Parse the logs to determine the status of dataset checks
    Return: { (ds_id, version): {'format': format, 'status': status} }
    version and format are '-' when not applicable or unknown.
    status is None if no status reported yet.
    """
    log_dir = args['--log-dir']
    ds_status_map = {}
    for path in sorted(glob.glob(join(log_dir, '*.log'))):
        with open(path) as f:
            for line in f:
                result = _analyze_log_line(line)
                if result is None:
                    continue
                ds_id = result.pop('ds_id')
                version = result.pop('version')
                ds_status_map[(ds_id, version)] = result
    return ds_status_map


def _index_result_logs(args):
    """
    Scan the log files and find the latest test migration results for every
    known dataset version. The latest information is returned; earlier results
    are skipped.
    Result format:
        {
            (ds_id, version): {
                'format': format,
                'status': status
                'filename': <log-filename>,
                'line_start': <1-based-line-number-of-first-line>,
                'line_end': <1-based-line-numberof-last-line>,
            },
            ...
        }
        version and format are '-' when not applicable or unknown.
        status is None if no status reported yet.
    The result is returned as an OrderedDict so that results from the same log
    file will be kept together during iteration (this is crucial.)
    """
    log_dir = args['--log-dir']
    ds_result_map = OrderedDict()
    for path in sorted(glob.glob(join(log_dir, '*.log'))):
        cur_result = None
        with open(path) as f:
            for line_num, line in enumerate(f, 1):
                result = _analyze_log_line(line)
                if result is None:
                    if cur_result is not None:
                        cur_result['line_end'] = line_num
                    continue
                cur_result = result
                ds_id = result.pop('ds_id')
                version = result.pop('version')
                result['filename'] = path
                result['line_start'] = line_num
                result['line_end'] = line_num
                ds_result_map.pop((ds_id, version), None)
                ds_result_map[(ds_id, version)] = result
    return ds_result_map


def _read_ds_ids_versions(filename):
    """Return [(ds_id, [version, ...]), ...]"""
    ds_id_versions_list = []
    with open(filename) as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            ds_id = parts[0]
            # Filter out bogus dataset IDs that might have crept in
            if not re.match(DS_ID_PATTERN + '$', ds_id):
                continue
            versions = parts[1:]
            if not versions:
                versions.append('master__tip')
            ds_id_versions_list.append((ds_id, versions))
    return ds_id_versions_list


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


def _check_ds_diagnosis(info, format):
    if info['writeflag']:
        raise Exception("Non-empty writeflag present.")
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


def _get_zz9_store(config):
    store_config = config['store_config']
    return zz9d.stores.get_store(store_config)


def _get_datamap_path(config, ds_id, version):
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    version_src = join(ro_repo_dir, 'versions', version)
    datamap_path = join(version_src, 'datamap.zz9')
    return datamap_path


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


def _get_version_format_map(config, ds_id, versions):
    """Get format of each version of interest"""
    ro_repo_dir = _get_readonly_zz9repo_dir(config, ds_id)
    try:
        existing_versions = set(os.listdir(join(ro_repo_dir, 'versions')))
    except OSError:
        return None
    version_format_map = {}
    for version in versions:
        if version not in existing_versions:
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
    assert os.path.isdir(config['read_only_zz9repo'])
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
        # Some command other than 'list' or 'detect'
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
    return _do_command(args)


if __name__ == '__main__':
    sys.exit(main())
