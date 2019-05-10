"""
Read backend server logs and save HTTP request history to sqlite DB

Usage:
    scan_http_logs.py [options] <command>


Options:
    --db-filename=DB_FILENAME   [default: cr-server-requests.db]
    --test                      Run some internal self-checks
    --log-root-dir=DIRNAME      [default: /var/log/remote]
    --subdir-pattern=PATTERN    [default: eu-backend-*]
    --logfile-pattern=PATTERN   [default: other.log*]
    --verbose                   Print debug messages to stderr
    --num-days=N                Scan last N days of log files. [default: 7]
    --include-undated           Scan files without date in name

Commands:
    list        Print names of files that would be scanned
    scan        Scan log files and store records in DB
    test        Run limited internal self-check

Notes:
    If a log filename ends with ".gz" it is assumed to be gzipped.
    If the database file doesn't exist, it is created.
"""
from __future__ import print_function
import codecs
from contextlib import closing
from datetime import date, datetime, timedelta
import glob
import os
import re
import gzip
import sqlite3
import sys

import docopt

# Some awkwardness to support both Python 2 and Python 3 without using six
PY2 = sys.version_info.major == 2


SQL_SETUP_SCRIPT = """
CREATE TABLE IF NOT EXISTS cr_server_requests (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    auth_token_prefix TEXT,
    req_timestamp TIMESTAMP,
    http_verb TEXT,
    req_path TEXT,
    http_status INTEGER,
    user_agent TEXT,
    dataset_id TEXT
);

CREATE INDEX IF NOT EXISTS cr_server_requests_ts_idx ON cr_server_requests(req_timestamp);

CREATE INDEX IF NOT EXISTS cr_server_requests_ds_idx ON cr_server_requests(dataset_id);

CREATE TABLE IF NOT EXISTS cr_server_logfiles (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    num_requests INTEGER NOT NULL,
    parsed_timestamp TIMESTAMP
);
"""

# Example log line:
'''2019-05-09T18:30:46.281931+00:00 alpha-backend-4-212 supervisord: cr.server-03 73.78.228.168 - token:1085023f74234916a962ec08fe9b9382/userid:2558f05f81df4684917f4205452daa76 [2019-05-09 18:30:46.280942] "GET /api/projects/d273f4ddb6b94b63a4f05609cb5fdb89/ HTTP/1.0" 200 1001 "http://local.crunch.io:8000/d273f4ddb6b94b63a4f05609cb5fdb89" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"'''  # noqa: B950

HTTP_REQUEST_PATTERN = re.compile(
    r"""
    (?P<ip_addr>\S+)
    \s+
    (?P<unused_ident>\S+)
    \s+
    (?P<user_id>\S+)
    \s+
    \[(?P<req_timestamp>.+?)\]
    \s+
    "(?P<http_verb>\S+)\ (?P<req_path>/\S+)\ HTTP/.+?"
    \s+
    (?P<http_status>\d{3})
    \s+
    (?P<resp_size>\d+)
    \s+
    "(?P<http_referrer>.*?)"
    \s+
    "(?P<user_agent>.*?)"
    """,
    re.VERBOSE,
)


def main():
    args = docopt.docopt(__doc__)
    command = args["<command>"]
    if command == "list":
        return do_list(args)
    elif command == "scan":
        return do_scan(args)
    elif command == "test":
        return do_test(args)
    else:
        raise ValueError("Invalid command: {}".format(command))


def do_list(args):
    for log_filename in list_filtered_logfiles(args):
        print(log_filename)


def do_scan(args):
    num_requests = 0
    db_filename = args["--db-filename"]
    print("Opening database file:", db_filename)
    conn = sqlite3.connect(
        db_filename, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    try:
        ensure_schema(conn)
        log_root_dir = get_root_dir(args)
        print("Scanning log files under", log_root_dir)
        log_filenames = list_filtered_logfiles(args)
        for log_filename in log_filenames:
            num_requests += parse_log_file(conn, log_filename)
    finally:
        conn.close()
    print("Recorded {} requests found in the log files.".format(num_requests))
    return 0


def do_test(args):
    test_parse_timestamp()
    print("Ok")
    return 0


################################################################################
# Helper functions

# The date embedded in a log filename reflects the timestamps in the
# lines at the end of that file, not the beginning.
DATE_PATTERN = re.compile(r"-(?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})")


def list_filtered_logfiles(args):
    verbose = args["--verbose"]
    log_root_dir = get_root_dir(args)
    if not os.path.exists(log_root_dir):
        raise ValueError("Missing log root dir: {}".format(log_root_dir))
    full_pattern = os.path.join(
        log_root_dir, args["--subdir-pattern"], args["--logfile-pattern"]
    )
    num_days = int(args["--num-days"])
    today = date.today()
    interval = timedelta(num_days)
    result = []
    if verbose:
        print("Log filename pattern:", full_pattern, file=sys.stderr)
    for log_filename in glob.glob(full_pattern):
        m = DATE_PATTERN.search(os.path.basename(log_filename))
        if not m:
            if not args["--include-undated"]:
                if verbose:
                    print("Skipping undated log file:", log_filename, file=sys.stderr)
                continue
            # No date in filename, assume it is from today
            logfile_date = today
        else:
            logfile_date = date(
                int(m.group("year")), int(m.group("month")), int(m.group("day"))
            )
        if today - logfile_date <= interval:
            result.append((logfile_date, log_filename))
        elif verbose:
            print("Filtered out by date:", log_filename, file=sys.stderr)
    result.sort()
    return [i[1] for i in result]


def get_root_dir(args):
    return os.path.abspath(os.path.expanduser(args["--log-root-dir"]))


def ensure_schema(conn):
    with closing(conn.cursor()) as cur:
        cur.executescript(SQL_SETUP_SCRIPT)
    conn.commit()


def parse_log_file(conn, log_filename):
    with closing(conn.cursor()) as cur:
        cur.execute(
            """
            SELECT num_requests, parsed_timestamp FROM cr_server_logfiles
            WHERE filename=?
            """,
            (log_filename,),
        )
        row = cur.fetchone()
        if row is not None:
            print(
                "Already parsed {} requests from {} on {}".format(
                    row[0], log_filename, row[1]
                )
            )
            return 0
    print("Parsing log file:", log_filename)
    try:
        fileobj = open(log_filename, "rb")
        if log_filename.endswith(".gz"):
            line_iter = gzip.GzipFile(log_filename, "rb", fileobj=fileobj)
        else:
            line_iter = iter(fileobj)
        try:
            num_requests = parse_log_lines(conn, line_iter)
        finally:
            fileobj.close()
        with closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO cr_server_logfiles (filename, num_requests, parsed_timestamp)
                VALUES (?, ?, ?)
                """,
                (log_filename, num_requests, datetime.now()),
            )
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    return num_requests


def parse_log_lines(conn, line_iter):
    num_requests = 0
    with closing(conn.cursor()) as cur:
        for line_num, line in enumerate(line_iter, 1):
            line = to_str(line)
            m = HTTP_REQUEST_PATTERN.search(line)
            if not m:
                continue
            try:
                record_request(cur, m.groupdict())
            except Exception:
                print("Error on line", line_num, file=sys.stderr)
                raise
            num_requests += 1
    return num_requests


def to_str(b):
    if PY2:
        return b
    return codecs.decode(b, "utf-8", "backslashreplace")


def record_request(cur, data):
    req_timestamp = parse_timestamp(data["req_timestamp"])
    http_status = int(data["http_status"])
    generate_crunch_info(data)
    cur.execute(
        """
        INSERT INTO
        cr_server_requests(
            user_id,
            auth_token_prefix,
            req_timestamp,
            http_verb,
            req_path,
            http_status,
            user_agent,
            dataset_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["user_id"],
            data["auth_token_prefix"],
            req_timestamp,
            data["http_verb"],
            data["req_path"],
            http_status,
            data["user_agent"],
            data["dataset_id"],
        ),
    )


ISO_TIMESTAMP_PATTERN = re.compile(
    r"""
    (?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})
    [ T]
    (?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})
    (?:[,.](?P<fraction_digits>\d+))?
    \s? # optional space before timezone offset
    (?:(?P<tz_sign>[+-])(?P<tz_hours>\d{2}):?(?P<tz_minutes>\d{2}))?
    """,
    re.VERBOSE,
)

APACHE_TIMESTAMP_PATTERN = re.compile(
    r"""
    (?P<day>\d{2})/(?P<month_str>\S+)/(?P<year>\d{4})
    :(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})
    (?:\s(?P<tz_sign>[+-])(?P<tz_hours>\d{2}):?(?P<tz_minutes>\d{2}))?
    """,
    re.VERBOSE,
)


def parse_timestamp(timestamp_str):
    """
    Parse a timestamp from a log line.
    Return a datetime object if it is valid,
    or raise ValueError if it is not recognized.

    If the timestamp includes a timezone offset (e.g. -0400)
    then the resulting datetime is converted to UTC time.
    """
    non_numeric_month = False
    m = ISO_TIMESTAMP_PATTERN.match(timestamp_str)
    if not m:
        non_numeric_month = True
        m = APACHE_TIMESTAMP_PATTERN.match(timestamp_str)
    if not m:
        raise ValueError("Timestamp format not recognized: {}".format(timestamp_str))
    data = m.groupdict()
    year = int(data["year"])
    day = int(data["day"])
    if non_numeric_month:
        month = datetime.strptime(data["month_str"], "%b").month
    else:
        month = int(data["month"])
    hour = int(data["hour"])
    minute = int(data["minute"])
    second = int(data["second"])
    microsecond = 0
    fraction_digits = data.get("fraction_digits")
    if fraction_digits:
        fraction_digits = fraction_digits[:6]
        microsecond = int(fraction_digits) * 10 ** (6 - len(fraction_digits))
    t = datetime(year, month, day, hour, minute, second, microsecond)
    tz_sign = data.get("tz_sign")
    if not tz_sign:
        return t
    d = timedelta(hours=int(data["tz_hours"]), minutes=int(data["tz_minutes"]))
    if not d:
        return t
    if tz_sign == "-":
        return t + d
    return t - d


def test_parse_timestamp():
    print("test_parse_timestamp")
    # Test the new HTTP request timestamp format
    assert parse_timestamp("2019-05-09 18:30:46.280942") == datetime(
        2019, 5, 9, 18, 30, 46, 280942
    )
    # Make sure we can handle just 3 digits in fractional part
    assert parse_timestamp("2019-05-07 14:25:32.967") == datetime(
        2019, 5, 7, 14, 25, 32, 967000
    )  # converts milliseconds to microseconds
    # Make sure we can handle the old cr.server request timestamp format
    assert parse_timestamp("08/May/2019:21:03:49") == datetime(2019, 5, 8, 21, 3, 49)
    # Make sure we can parse the full ISO timestamp at front of log lines
    assert parse_timestamp("2019-05-09T18:30:46.281931+00:00") == datetime(
        2019, 5, 9, 18, 30, 46, 281931
    )
    # Try a positive timezone offset
    assert parse_timestamp("2019-05-09T18:30:46.281931+02:00") == datetime(
        2019, 5, 9, 16, 30, 46, 281931
    )
    # Make sure we also handle the "standard" Apache Common Log format
    assert parse_timestamp("10/Oct/2000:13:55:36 -0700") == datetime(
        2000, 10, 10, 20, 55, 36
    )  # converts to UTC
    # Bonus: we can handle the output of "date --iso-8601=ns"
    assert parse_timestamp("2019-05-09T17:27:19,064360678-04:00") == datetime(
        2019, 5, 9, 21, 27, 19, 64360
    )  # converts to UTC, truncates digits beyond microseconds
    # Don't allow garbage
    try:
        parse_timestamp("blah")
    except ValueError:
        pass
    else:
        raise AssertionError("blah is not a valid timestamp")


DATASET_ID_PATTERN = re.compile(r"/datasets/(.*?)/")


def generate_crunch_info(data):
    """Mutates the data dictionary, adding Crunch-specific fields"""
    # Get the dataset ID
    m = DATASET_ID_PATTERN.search(data["req_path"])
    if m:
        data["dataset_id"] = m.group(1)
    else:
        data["dataset_id"] = None
    # Split auth token from user ID
    first_part, _, second_part = data["user_id"].partition("/")
    auth_token_prefix_len = 8
    if first_part.startswith("token:") and second_part.startswith("userid:"):
        data["auth_token_prefix"] = first_part[
            len("token:") : len("token:") + auth_token_prefix_len
        ]
        data["user_id"] = second_part[len("userid:") :]
    else:
        data["auth_token_prefix"] = None
        data["user_id"] = None


if __name__ == "__main__":
    sys.exit(main())
