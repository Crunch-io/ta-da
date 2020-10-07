#!/var/lib/crunch.io/venv/bin/python
"""
Control a fix_datamap.py process running on a zz9 server from a backend server

Communication is through files visible to both processes in EFS:

    Input file read by drive_fix_datamap.py:
        <dataset-id>@<node-id>[:<scan-status>]

    Send file written by drive_fix_datamap, read by fix_datamap.py --stream:
        <timestamp> <dataset-id>@<node-id>

    Done file written by fix_datamap.py --stream, read by drive_fix_datamap.py:
        <timestamp> <dataset-id>@<node-id>:<repair-status>

Usage:
    drive_fix_datamap.py [options] <input-file> <send-file> <done-file>

Options:
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]
"""
# Control flow
##############
# drive_fix_datamap.py running on a backend server:
#   Open Input file for read
#   Read (ds_id, node_id) pairs from Input file, group by ds_id
#   For each ds_id:
#       If dataset ds_id is available, make it unavailable
#       Inside try-block:
#           Run ds.retire()
#           For each node_id for that ds_id:
#               Append "<timestamp> <dataset-id>@<node-id>" to Send file
#               Wait for "<timestamp> <dataset-id>@<node-id>:<status>" in Done file
#       Inside finally block:
#           Make dataset available if it was originally unavailable
#
# fix_datamap.py --stream running on a zz9 server:
#   Read (timestamp, dataset_id, node_id) tuples from Send file into a queue
#   Eliminate (timestamp, dataset_id, node_id) tuples from queue found in Done file
#   Loop:
#       Take a (timestamp, dataset_id, node_id) tuple from the queue
#       Attempt datamap repair for that dataset/node and generate status
#       Append "<timestamp> <dataset-id>@<nodeid>:<status>" to Done file
from __future__ import print_function
from collections import OrderedDict
from datetime import datetime
import errno
import os
import re
import sys
import time

import docopt
from magicbus import bus
from magicbus.plugins import loggers
import six

from cr.lib import actions
from cr.lib.commands.common import load_settings, startup
from cr.lib.entities.datasets.dataset import Dataset
from cr.lib import exceptions
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

INPUT_PATTERN = re.compile(r"^(?P<ds_id>\w+)@(?P<node_id>[^: ]*)(:(?P<status>.*))?$")

REPAIRABLE_STATUS_PATTERN = re.compile(r"ERROR (\d+) columns with errors")


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    settings.update(load_settings(settings_yaml))
    startup()


def _read_input_ids(input_filename):  # noqa: C901
    # Read the <dataset-id>@<node-id> pairs to process.
    # Map ds_id to list of node_ids using OrderedDict to preserve dataset order
    # If status is given, skip lines except where status looks repairable:
    # "ERROR <n> columns with errors"
    input_ids = OrderedDict()
    deleted_datasets = None
    ok_versions = None
    non_repairable_versions = None
    with open(input_filename) as input_f:
        for line_num, line in enumerate(input_f, 1):
            line = line.strip()
            if not line:
                continue
            m = INPUT_PATTERN.match(line)
            if not m:
                raise ValueError(
                    "{}:{}: invalid format: {}".format(input_filename, line_num, line)
                )
            ds_id = m.group("ds_id")
            node_id = m.group("node_id")
            status = m.group("status")
            if status:
                if status == "DELETED":
                    if deleted_datasets is None:
                        deleted_datasets = 0
                    deleted_datasets += 1
                    continue
                if status == "OK":
                    if ok_versions is None:
                        ok_versions = 0
                    ok_versions += 1
                    continue
                m = REPAIRABLE_STATUS_PATTERN.match(status)
                if not m:
                    if non_repairable_versions is None:
                        non_repairable_versions = 0
                    non_repairable_versions += 1
                    continue
            input_ids.setdefault(ds_id, []).append(node_id)

    if deleted_datasets is not None:
        print("Filtered out {} DELETED datasets".format(deleted_datasets))
    if ok_versions is not None:
        print("Filtered out {} OK dataset versions".format(ok_versions))
    if non_repairable_versions is not None:
        print(
            "Filtered out {} non-repairable dataset versions".format(
                non_repairable_versions
            )
        )
    version_count = sum(len(v) for v in six.itervalues(input_ids))
    print(
        "Attempting to repair {} versions of {} datasets".format(
            version_count, len(input_ids)
        )
    )
    sys.stdout.flush()

    return input_ids


class DoneScanner(object):

    DONE_PATTERN = re.compile(
        r"^(?P<timestamp>\S+)\s+(?P<ds_id>\w+)@(?P<node_id>[^:]+):(?P<status>.*)$"
    )

    BUSY_PHASES = ("|", "/", "-", "\\")

    def __init__(self, done_filename, show_busy=True):
        self.done_filename = done_filename
        self.done_f = None
        self.show_busy = show_busy
        self.busy_phase_index = None

    def wait(self, timestamp, ds_id, node_id):
        """
        Wait until "<timestamp> <ds-id>@<node-id>:<status>" message is received.
        Return status.
        """
        # Wait till done file exists
        self._busy_init()
        while self.done_f is None:
            try:
                self.done_f = open(self.done_filename, "r")
            except IOError as err:
                if err.errno != errno.ENOENT:
                    raise
                self._busy_update()
                time.sleep(0.25)
        # Wait till expected message shows up in done file
        self._busy_done()
        while True:
            line = self.done_f.readline()
            if not line:
                # EOF, keep waiting for next line
                self._busy_update()
                time.sleep(0.25)
                continue
            m = self.DONE_PATTERN.match(line)
            if not m:
                raise ValueError(
                    "Line in done file not in right format: {}".format(line)
                )
            if (
                m.group("timestamp") == timestamp
                and m.group("ds_id") == ds_id
                and m.group("node_id") == node_id
            ):
                self._busy_done()
                return m.group("status")
            self._busy_update()

    def close(self):
        if self.done_f is not None:
            self.done_f.close()
            self.done_f = None

    def _busy_init(self):
        self.busy_phase_index = None

    def _busy_update(self):
        if not self.show_busy:
            return
        if self.busy_phase_index is None:
            self.busy_phase_index = 0
        else:
            sys.stdout.write("\b")  # backspace over previous marker
        sys.stdout.write(self.BUSY_PHASES[self.busy_phase_index])
        sys.stdout.flush()
        self.busy_phase_index += 1
        if self.busy_phase_index >= len(self.BUSY_PHASES):
            self.busy_phase_index = 0

    def _busy_done(self):
        if not self.show_busy:
            return
        if self.busy_phase_index is not None:
            sys.stdout.write("\b")  # backspace over previous marker
            sys.stdout.flush()
            self.busy_phase_index = None


def _attempt_remote_repair_datamap(send_f, done_scanner, ds_id, node_id):
    t = datetime.utcnow()
    timestamp = t.strftime(TIMESTAMP_FORMAT)
    msg = "{} {}@{}\n".format(timestamp, ds_id, node_id)
    print("Sending : {}".format(msg.rstrip()))
    sys.stdout.flush()
    send_f.write(msg)
    send_f.flush()
    os.fdatasync(send_f.fileno())
    status = done_scanner.wait(timestamp, ds_id, node_id)
    print("Received: {}".format(status))
    sys.stdout.flush()
    if status == "STOP":
        # The fix_datamap.py --stream script received Ctrl-C
        raise KeyboardInterrupt()


def _attempt_repair_dataset(send_f, done_scanner, input_ids, ds):
    was_maintenance = ds.maintenance
    got_lock = False
    if not was_maintenance:
        print("Putting dataset {} in maintenance mode".format(ds.id))
        sys.stdout.flush()
        ds.enter_maintenance()
    try:
        print("Locking dataset {} ...".format(ds.id), end="")
        sys.stdout.flush()
        with actions.dataset_lock("fix_datamap", ds.id, exclusive=True):
            got_lock = True
            print("locked.")
            print("Retiring dataset {}".format(ds.id))
            sys.stdout.flush()
            ds.retire()
            node_ids = input_ids[ds.id]
            for node_id in node_ids:
                _attempt_remote_repair_datamap(send_f, done_scanner, ds.id, node_id)
    finally:
        if got_lock:
            print("Unlocked dataset {}".format(ds.id))
            sys.stdout.flush()
        if ds.maintenance and not was_maintenance:
            print("Taking dataset {} out of maintenance mode".format(ds.id))
            sys.stdout.flush()
            ds.exit_maintenance()
    print()
    sys.stdout.flush()


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)

    input_filename = args["<input-file>"]
    send_filename = args["<send-file>"]
    done_filename = args["<done-file>"]

    input_ids = _read_input_ids(input_filename)
    done_scanner = DoneScanner(done_filename)
    try:
        with open(send_filename, "a") as send_f:
            for ds_id in input_ids:
                try:
                    ds = Dataset.find_by_id(id=ds_id, version="master__tip")
                except exceptions.NotFound:
                    print("Dataset {} not found, skipping".format(ds_id))
                    sys.stdout.flush()
                    continue
                _attempt_repair_dataset(send_f, done_scanner, input_ids, ds)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.stdout.flush()
    finally:
        done_scanner.close()


if __name__ == "__main__":
    sys.exit(main())
