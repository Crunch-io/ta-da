#!/usr/bin/env python3
"""
Scan a ZZ9 log file looking for activity related to a dataset.
"""
# Script written by David H in case you are wondering
# It uses f-strings so it really does require Python 3
from __future__ import print_function
import argparse
from datetime import datetime, timedelta
import gzip
import io
import os
import re
import sys
import time


def to_bytes(s):
    return s.encode("utf-8")


def to_str(b):
    return b.decode("utf-8", "replace")


class ZZ9LogScanner(object):

    # Example log line (combine the three lines below into one):
    # 2019-09-05T08:16:07.696840+00:00 alpha-zz9-247 supervisord: zz9-53
    # Factory tcp://10.30.2.247:22953?zz9ver=1&zz9ver=2&zz9ver=3 try leasing
    # 0af661b55a7d4aa78f336607b6f26c98

    log_pattern = re.compile(
        br"(?P<timestamp>\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)"
        br"(?:\+00:00)?"  # timezone offset which is ignored
        br" (?P<host>\S+)"
        br" (?P<app>\S+):"
        br" (?P<factory>\S+)"
        br" (?P<message>.*$)"
    )

    log_pattern_old = re.compile(
        br"(?P<month>\S\S\S) "
        br"(?P<day>(?:\d| )\d) "
        br"(?P<time>\d\d:\d\d:\d\d) "
        br"(?P<host>\S+) "
        br"(?P<app>\S+): "
        br"(?P<factory>\S+) "
        br"(?P<message>.*$)"
    )

    onesec = timedelta(seconds=1)

    def __init__(self, dataset_id, debug=False, now=None):
        self.dataset_id = dataset_id
        self.dataset_id_bytes = to_bytes(dataset_id)
        self.debug = debug
        #####
        self.zz9_factory = None
        self.prev_datetime = None
        self.ds_id_pattern = re.compile(
            br"\b%s\b" % (re.escape(self.dataset_id_bytes),)
        )
        self.lease_pattern = re.compile(
            br"\btry leasing %s\b" % (re.escape(self.dataset_id_bytes),)
        )
        self.map_del_pattern = re.compile(
            br"\bmap\.delete\(%s\)" % (re.escape(self.dataset_id_bytes),)
        )
        self.resources_pattern = re.compile(
            br"\bresources:.*\bdsids:.*\b%s\b" % (re.escape(self.dataset_id_bytes),)
        )
        if now is None:
            self.now = datetime.utcnow()
        else:
            self.now = now
        self.this_year = self.now.year
        self.last_year = self.now.year - 1
        self.prev_message_was_resources = None

    def __call__(self, line_iter):
        r"""line_iter yields bytestrings ending with b'\n'"""
        line_count = 0
        log_count = 0
        match_count = 0
        for line in line_iter:
            line_count += 1
            m = self.log_pattern.match(line)
            if not m:
                continue
            log_count += 1
            emit_line = False
            cur_factory = m.group("factory")
            message = m.group("message")
            if self.zz9_factory:
                if cur_factory == self.zz9_factory:
                    emit_line = True
                    if self.map_del_pattern.search(message):
                        self.zz9_factory = None
            if self.ds_id_pattern.search(message):
                emit_line = True
                if self.lease_pattern.search(message):
                    self.zz9_factory = cur_factory
            if not emit_line:
                continue
            match_count += 1
            if self.resources_pattern.search(message):
                cur_message_is_resources = True
            else:
                cur_message_is_resources = False
            cur_datetime = self._calc_cur_datetime(m)
            if (
                self.prev_datetime is not None
                and (cur_datetime - self.prev_datetime) > self.onesec
            ):
                if not self.prev_message_was_resources:
                    sys.stdout.write("\n")
            self.prev_message_was_resources = cur_message_is_resources
            self.prev_datetime = cur_datetime
            sys.stdout.write(to_str(line))
            sys.stdout.flush()
        self._print_stats(line_count, log_count, match_count)

    def _print_stats(self, line_count, log_count, match_count):
        if not self.debug:
            return
        print(
            f"Total lines parsed:     {line_count:7}\n"
            f"Log lines found:        {log_count:7}\n"
            f"Lines matching dataset: {match_count:7}",
            file=sys.stderr,
        )

    def _calc_cur_datetime(self, m):
        return datetime.strptime(to_str(m.group("timestamp")), "%Y-%m-%dT%H:%M:%S.%f")

    def _old_calc_cur_datetime(self, m):
        month_str = to_str(m.group("month"))
        month = datetime.strptime(month_str, "%b").month
        day_str = to_str(m.group("day"))
        day = int(day_str.strip())
        hms_str = to_str(m.group("time"))
        hms = datetime.strptime(hms_str, "%H:%M:%S")
        try:
            dt1 = datetime(self.this_year, month, day, hms.hour, hms.minute, hms.second)
        except ValueError:
            # Tried to create Feb. 29 on a non-leap year
            dt1 = None
        try:
            dt2 = datetime(self.last_year, month, day, hms.hour, hms.minute, hms.second)
        except ValueError:
            # Tried to create Feb. 29 on a non-leap year
            dt2 = None
        if dt1 is None or dt1 > self.now:
            assert dt2 is not None
            return dt2
        return dt1


def follow_file(filename, poll_interval=1.0, start_at_end=False):
    """
    Behave sort of like the "tail -F" command.
    Yield new lines from the file as they become available.
    Attempt to re-open the file if it disappears or is renamed.
    Run forever or until Ctrl-C is pressed (KeyboardInterrupt).
    """
    f = None
    f_inode = None
    try:
        while True:
            try:
                f = open(filename, "rb")
            except OSError:
                # Unfortunately, FileNotFoundError not available on Python 2.7
                time.sleep(poll_interval)
                continue
            if f_inode is None and start_at_end:
                f.seek(0, os.SEEK_END)
            f_inode = os.fstat(f.fileno()).st_ino
            while f is not None:
                line = f.readline()
                if line:
                    yield line
                    continue
                try:
                    cur_inode = os.stat(filename).st_ino
                except OSError:
                    cur_inode = None
                if cur_inode != f_inode:
                    # The file has disappeared or has been renamed
                    f.close()
                    f = None
                else:
                    time.sleep(poll_interval)
    except KeyboardInterrupt:
        return
    finally:
        if f is not None:
            f.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-d",
        "--debug",
        help="Print some messages to help debug this script",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--scroll-to-end",
        help="Scroll to end of file before following",
        action="store_true",
    )
    parser.add_argument(
        "-f", "--follow", help="Follow log file (like `tail -F`)", action="store_true"
    )
    parser.add_argument("dataset_id", help="Select log messages for this dataset")
    parser.add_argument(
        "input_filename", help="Name of log file, or '-' for standard input", nargs="+"
    )
    args = parser.parse_args()
    for file_num, input_filename in enumerate(args.input_filename, 1):
        do_follow = args.follow and file_num == len(args.input_filename)
        fileobj = None
        line_iter = None
        if input_filename == "-":
            if isinstance(sys.stdin, io.TextIOWrapper):
                line_iter = sys.stdin.detach()
            else:
                line_iter = iter(sys.stdin)
        elif do_follow:
            line_iter = follow_file(input_filename, start_at_end=args.scroll_to_end)
        else:
            fileobj = open(input_filename, "rb")
            if input_filename.endswith(".gz"):
                line_iter = gzip.GzipFile(input_filename, "rb", fileobj=fileobj)
            else:
                line_iter = iter(fileobj)
        try:
            ZZ9LogScanner(args.dataset_id, debug=args.debug)(line_iter)
        finally:
            if fileobj is not None:
                fileobj.close()


if __name__ == "__main__":
    sys.exit(main())
