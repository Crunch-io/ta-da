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
    --num-days=N                Scan N days of log files. [default: 7]
    --start-date=YYYYMMDD       Starting date pattern
                                (default: N days before today)
    --include-undated           Scan files without date in name
    --pool-size=N               Run N parsing processes [default: 1]
    --skip-cleanup              Don't remove intermediate files

Commands:
    list        Print names of files that could be scanned
    scan        Scan log files and store records in DB
    test        Run limited internal self-check

Notes:
    If a log filename ends with ".gz" it is assumed to be gzipped.
    If the database file doesn't exist, it is created.
"""
from __future__ import print_function
import codecs
from contextlib import closing
import csv
from datetime import date, datetime, timedelta
import glob
import os
import re
import gzip
from multiprocessing import Pool
import sqlite3
import sys
import tempfile
import time
import traceback

import docopt

# Some awkwardness to support both Python 2 and Python 3 without using six
PY2 = sys.version_info.major == 2


SQL_SETUP_SCRIPT = """
CREATE TABLE IF NOT EXISTS cr_server_logfiles (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    state TEXT,
    updated_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cr_server_requests (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES cr_server_logfiles(id),
    line_num INTEGER,
    user_id TEXT,
    auth_token_prefix TEXT,
    req_timestamp TIMESTAMP,
    http_verb TEXT,
    req_path TEXT,
    http_status INTEGER,
    user_agent TEXT,
    dataset_id TEXT
);

CREATE INDEX IF NOT EXISTS cr_server_requests_ts_idx
ON cr_server_requests(req_timestamp);

CREATE INDEX IF NOT EXISTS cr_server_requests_ds_idx ON cr_server_requests(dataset_id);
"""

CSV_FIELD_NAMES = [
    "file_id",
    "line_num",
    "user_id",
    "auth_token_prefix",
    "req_timestamp",
    "http_verb",
    "req_path",
    "http_status",
    "user_agent",
    "dataset_id",
]

# Example log lines (see test_parse_log_lines()):
line1 = '''2019-05-09T18:30:46.281931+00:00 alpha-backend-4-212 supervisord: cr.server-03 73.78.228.168 - token:1085023f74234916a962ec08fe9b9382/userid:2558f05f81df4684917f4205452daa76 [2019-05-09 18:30:46.280942] "GET /api/projects/d273f4ddb6b94b63a4f05609cb5fdb89/ HTTP/1.0" 200 1001 "http://local.crunch.io:8000/d273f4ddb6b94b63a4f05609cb5fdb89" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"'''  # noqa: B950
line2 = '''May  6 15:02:08 eu-backend-5-171 supervisord: cr.server-14 38.99.85.65 - token:5bd2dd2ca32d4d8dbbaae6201ef60fc8/userid:80899091624a41a8b96331a369f1bd88 [06/May/2019:15:02:08] "POST /api/datasets/fa19d320ae2f461ea555043700d692d5/stream/ HTTP/1.0" 204 - "" "pycrunch/0.4.11"'''  # noqa: B950
line3 = """blah"""

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
    (?P<resp_size>\d+|-)
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
    db_filename = os.path.expanduser(args["--db-filename"])
    pool_size = int(args["--pool-size"])
    log_root_dir = get_root_dir(args)
    print("Opening database file:", db_filename)
    conn = sqlite3.connect(
        db_filename, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    try:
        ensure_schema(conn)
        print("Scanning log files under", log_root_dir)
        log_filenames = list_filtered_logfiles(args)
        t0 = time.time()
        param_list = create_parse_param_list(conn, log_filenames, db_filename)
        if pool_size > 1:
            p = Pool(pool_size)
            result = sorted(p.imap_unordered(parse_log_file, param_list))
        else:
            result = sorted(parse_log_file(param) for param in param_list)
        print("Parsed", len(result), "files in", time.time() - t0, "seconds")
        t0 = time.time()
        ingest_parsed_files(
            conn, result, cleanup_csv_files=(not args["--skip-cleanup"])
        )
        print("Ingested", len(result), "files in", time.time() - t0, "seconds")
    finally:
        conn.close()
    return 0


def do_test(args):
    test_parse_timestamp()
    test_parse_log_lines()
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
    start_date_str = args["--start-date"]
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y%m%d").date()
        end_date = start_date + timedelta(num_days)
    else:
        end_date = date.today()
        start_date = end_date - timedelta(num_days)
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
            # No date in filename - give it an arbitrary date for sorting purposes
            logfile_date = end_date
        else:
            logfile_date = date(
                int(m.group("year")), int(m.group("month")), int(m.group("day"))
            )
            if not (start_date <= logfile_date <= end_date):
                if verbose:
                    print("Filtered out by date:", log_filename, file=sys.stderr)
                continue
        result.append((logfile_date, log_filename))
    result.sort()
    return [i[1] for i in result]


def get_root_dir(args):
    return os.path.abspath(os.path.expanduser(args["--log-root-dir"]))


def ensure_schema(conn):
    with closing(conn.cursor()) as cur:
        cur.executescript(SQL_SETUP_SCRIPT)
    conn.commit()


def parse_log_file(param):
    """
    param: (sequence_num, file_id, log_filename, db_filename)
    Return (sequence_num, file_id, temp_csv_filename)
    """
    try:
        sequence_num, file_id, log_filename, db_filename = param
        temp_csv_filename = _parse_log_file(log_filename, file_id, db_filename)
        return (sequence_num, file_id, temp_csv_filename)
    except Exception:
        # If we don't print the stack trace here, multiprocessing will swallow
        # the traceback and we'll never see it, only the exception type.
        traceback.print_exc()
        raise


def _parse_log_file(log_filename, file_id, db_filename):
    """Return temp_csv_filename"""
    print("Parsing:", log_filename)
    csv_prefix = os.path.splitext(os.path.basename(db_filename))[0]
    with tempfile.NamedTemporaryFile(
        "wb",
        prefix=csv_prefix + "-",
        suffix=".csv",
        dir=os.path.dirname(db_filename),
        delete=False,
    ) as f:
        csv_writer = csv.DictWriter(f, CSV_FIELD_NAMES, extrasaction="ignore")
        csv_writer.writeheader()
        fileobj = open(log_filename, "rb")
        if log_filename.endswith(".gz"):
            line_iter = gzip.GzipFile(log_filename, "rb", fileobj=fileobj)
        else:
            line_iter = iter(fileobj)
        try:
            parse_log_lines(csv_writer, file_id, line_iter)
        finally:
            fileobj.close()
    return f.name


def create_parse_param_list(conn, log_filenames, db_filename):
    """Create a list of parameters, each suitable for parse_log_file"""
    parse_param_list = []
    for sequence_num, log_filename in enumerate(log_filenames, 1):
        file_id, prev_state = begin_parsing_log(conn, log_filename)
        if prev_state is not None:
            print(
                "Log file {} state is '{}', skipping".format(log_filename, prev_state),
                file=sys.stderr,
            )
            continue
        parse_param_list.append((sequence_num, file_id, log_filename, db_filename))
    return parse_param_list


def ingest_parsed_files(conn, parse_results, cleanup_csv_files=True):
    for _, file_id, csv_filename in parse_results:
        update_log_state(conn, file_id, "INGESTING", "PARSING")
        try:
            ingest_csv_file(conn, csv_filename)
        except BaseException:
            update_log_state(conn, file_id, "ERROR", "INGESTING")
            raise
        else:
            update_log_state(conn, file_id, "DONE", "INGESTING")
            if cleanup_csv_files:
                print("Removing:", csv_filename)
                os.remove(csv_filename)


def ingest_csv_file(conn, csv_filename):
    print("Ingesting:", csv_filename)
    with open(csv_filename, "rb") as f:
        r = csv.DictReader(f)
        try:
            with closing(conn.cursor()) as cur:
                cur.execute("BEGIN")  # start a transaction
                for row in r:
                    record_request_in_db(cur, row)
        except BaseException:
            conn.rollback()
            raise
        else:
            conn.commit()


def begin_parsing_log(conn, log_filename):
    """
    Record the fact that we are beginning to parse a log file.
    If the log file record already exists and has a non-NULL, non-empty state,
    don't change the state.  Otherwise, change the state to "PARSING".
    Return (file_id, prev_state) of the log file record.
    """
    filename_key = normalize_log_filename(log_filename)
    new_state = "PARSING"
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("BEGIN")  # start a transaction
            cur.execute(
                "SELECT id, state FROM cr_server_logfiles WHERE filename=?",
                (filename_key,),
            )
            row = cur.fetchone()
            if row is None:
                # No record for this log file exists
                cur.execute(
                    """
                    INSERT INTO cr_server_logfiles
                    (filename, state, updated_timestamp)
                    VALUES
                    (?, ?, ?)
                    """,
                    (filename_key, new_state, datetime.now()),
                )
                file_id = cur.lastrowid
                prev_state = None
            else:
                file_id, prev_state = row
                if not prev_state:
                    cur.execute(
                        """
                        UPDATE cr_server_logfiles SET state=?, updated_timestamp=?
                        WHERE id=?
                        """,
                        (new_state, datetime.now(), file_id),
                    )
    finally:
        conn.commit()
    return file_id, prev_state


def update_log_state(conn, file_id, new_state, expected_prev_state):
    """
    Set the parsing state of a log file if the previous state is as expected.
    new_state:
        "PARSING" to start parsing log file
        "INGESTING" for ingesting parse result csv files
        "DONE" to record that it is finished
        "ERROR" to record that it couldn't be parsed
    expected_prev_state:
        If the state doesn't match expected_prev_state, raise RuntimeError.
    """
    try:
        with closing(conn.cursor()) as cur:
            cur.execute("BEGIN")  # start a transaction
            cur.execute("SELECT state FROM cr_server_logfiles WHERE id=?", (file_id,))
            row = cur.fetchone()
            if row is None:
                # No record for this log file exists
                raise RuntimeError(
                    "Record for Log file ID {} disappeared".format(file_id)
                )
            prev_state = row[0]
            if prev_state != expected_prev_state:
                msg = "Log file ID {} in unexpected state '{}'".format(
                    file_id, prev_state
                )
                raise RuntimeError(msg)
            cur.execute(
                """
                UPDATE cr_server_logfiles SET state=?, updated_timestamp=?
                WHERE id=?
                """,
                (new_state, datetime.now(), file_id),
            )
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()


def normalize_log_filename(log_filename):
    if log_filename.endswith(".gz"):
        log_filename = log_filename[:-3]
    return os.path.normpath(os.path.abspath(log_filename))


def parse_log_lines(csv_writer, file_id, line_iter):
    num_requests = 0
    for line_num, line in enumerate(line_iter, 1):
        line = to_str(line)
        m = HTTP_REQUEST_PATTERN.search(line)
        if not m:
            continue
        try:
            data = m.groupdict()
            t = parse_timestamp(data["req_timestamp"])
            data["file_id"] = file_id
            data["line_num"] = line_num
            data["req_timestamp"] = t.strftime("%Y-%m-%d %H:%M:%S.%f")
            generate_crunch_info(data)
            csv_writer.writerow(data)
        except Exception:
            print("Error parsing file ID", file_id, "line", line_num, file=sys.stderr)
            raise
        num_requests += 1
    return num_requests


def to_str(b):
    if PY2:
        return b
    return codecs.decode(b, "utf-8", "backslashreplace")


def record_request_in_db(cur, data):
    """Store a CSV row in the requests database table"""
    file_id = int(data["file_id"])
    line_num = int(data["line_num"])
    req_timestamp = datetime.strptime(data["req_timestamp"], "%Y-%m-%d %H:%M:%S.%f")
    http_status = int(data["http_status"])
    row = (
        file_id,
        line_num,
        data["user_id"],
        data["auth_token_prefix"],
        req_timestamp,
        data["http_verb"],
        data["req_path"],
        http_status,
        data["user_agent"],
        data["dataset_id"],
    )
    cur.execute(
        """
        INSERT INTO cr_server_requests
        (
            file_id,
            line_num,
            user_id,
            auth_token_prefix,
            req_timestamp,
            http_verb,
            req_path,
            http_status,
            user_agent,
            dataset_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        row,
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


def test_parse_log_lines():
    print("test_parse_log_lines")
    m = HTTP_REQUEST_PATTERN.search(line1)
    assert m.group("ip_addr") == "73.78.228.168"
    assert (
        m.group("user_id")
        == "token:1085023f74234916a962ec08fe9b9382/userid:2558f05f81df4684917f4205452daa76"  # noqa: B950
    )
    assert m.group("req_timestamp") == "2019-05-09 18:30:46.280942"
    assert m.group("http_verb") == "GET"
    assert m.group("req_path") == "/api/projects/d273f4ddb6b94b63a4f05609cb5fdb89/"
    assert m.group("http_status") == "200"
    assert m.group("resp_size") == "1001"
    assert (
        m.group("user_agent")
        == "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"  # noqa: B950
    )

    m = HTTP_REQUEST_PATTERN.search(line2)
    assert m.group("ip_addr") == "38.99.85.65"
    assert (
        m.group("user_id")
        == "token:5bd2dd2ca32d4d8dbbaae6201ef60fc8/userid:80899091624a41a8b96331a369f1bd88"  # noqa: B950
    )
    assert m.group("req_timestamp") == "06/May/2019:15:02:08"
    assert m.group("http_verb") == "POST"
    assert (
        m.group("req_path")
        == "/api/datasets/fa19d320ae2f461ea555043700d692d5/stream/"  # noqa: B950
    )
    assert m.group("http_status") == "204"
    assert m.group("resp_size") == "-"
    assert m.group("user_agent") == "pycrunch/0.4.11"

    m = HTTP_REQUEST_PATTERN.search(line3)
    assert m is None


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
