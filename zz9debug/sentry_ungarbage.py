#!/usr/bin/env python
"""
Convert Sentry "raw" display of Python dictionary values from garbage into
something usable.
"""
from __future__ import print_function
import argparse
import ast
import json
import pprint
import sys

import six

DEFAULT_FORMAT = "python"

HINTS = """
Pass "-" for filename to read from standard input.
Paste the Sentry-mangled garbage and press Ctrl-D for EOF.
This script will print the input reformatted usefully.
"""


class ParsingError(Exception):
    pass


TEST_VECTORS = [
    (
        """ {"'txid'":"u'0000R9'","'frame'":"'primary'","'client_timeout'":900} """,
        {"txid": "0000R9", "frame": "primary", "client_timeout": 900},
    ),
    ("""{"'description'":"u''"}""", {"description": ""}),
    ("""\"u'play_workflow:9a6122deeeXXX'\"""", "play_workflow:9a6122deeeXXX"),
    (
        """["'/var/lib/crunch.io/venv/bin/cr.server.worker'","""
        """\"'/var/lib/crunch.io/cr.server.conf'","""
        """\"'--queues=ZZ9'"]""",
        [
            "/var/lib/crunch.io/venv/bin/cr.server.worker",
            "/var/lib/crunch.io/cr.server.conf",
            "--queues=ZZ9",
        ],
    ),
    ("blah", ParsingError),
    ("", ParsingError),
]


def _un_str(obj):  # noqa: C901
    while isinstance(obj, six.string_types):
        while obj.startswith(("'", "u'")) and obj.endswith("'"):
            try:
                obj = ast.literal_eval(obj)
                break
            except SyntaxError:
                # Just strip off opening and closing quotes
                if obj.startswith("u'"):
                    obj = obj[2:]
                else:
                    obj = obj[1:]
                obj = obj[:-1]
        if not isinstance(obj, six.string_types):
            continue
        if obj.startswith('{"u') and obj.endswith("}"):
            obj = ast.literal_eval(obj)
            continue
        if obj.startswith("{u'") and obj.endswith("}"):
            obj = ast.literal_eval(obj)
            continue
        if obj.startswith('["u') and obj.endswith("]"):
            obj = ast.literal_eval(obj)
            continue
        # Maybe it is a legit string
        return obj
    if isinstance(obj, dict):
        result = {}
        for key, value in six.iteritems(obj):
            key = _un_str(key)
            assert isinstance(key, six.string_types)
            result[key] = _un_str(value)
        return result
    elif isinstance(obj, list):
        result = []
        for item in obj:
            result.append(_un_str(item))
        return result
    else:
        return obj


def _process_input(blob):
    blob = blob.strip()
    if not blob:
        raise ParsingError("Empty input")

    # First step is to load text as json
    try:
        obj = json.loads(blob)
    except ValueError as err:
        raise ParsingError("JSON parsing error: {}".format(err))

    # Un-str() everything that looks like it has been str()'d
    result = _un_str(obj)
    return result


def test():
    for test_num, (input_str, expected_output) in enumerate(TEST_VECTORS, 1):
        print("Test #{}: ".format(test_num), end="")
        output = None
        try:
            output = _process_input(input_str)
        except ParsingError as err:
            output = err
        if isinstance(expected_output, (dict, list, str, int)):
            if output == expected_output:
                print("Ok")
                continue
        elif issubclass(expected_output, ParsingError):
            if isinstance(output, ParsingError):
                print("Ok")
                continue
        print("Failed")
        raise AssertionError(
            "Test #{}:\n"
            "Input:\n{}\n"
            "Output:\n{!r}\n"
            "Expected output:\n{!r}\n".format(
                test_num, input_str, output, expected_output
            )
        )
    print("Done.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=HINTS)
    parser.add_argument("filename", help='Name of input file or "-" for stdin. ')
    parser.add_argument(
        "--format",
        default=DEFAULT_FORMAT,
        help='Output format, "json" or "python". Default: {}'.format(DEFAULT_FORMAT),
    )
    parser.add_argument("--test", action="store_true", help="Run internal tests")
    args = parser.parse_args()
    if args.test:
        return test()
    if args.filename == "-":
        f = sys.stdin
    else:
        f = open(args.filename)
    try:
        blob = f.read()
        try:
            output = _process_input(blob)
        except ParsingError as err:
            print(str(err), file=sys.stderr)
            return 1
        if isinstance(output, str):
            sys.stdout.write(output)
        else:
            if args.format == "json":
                json.dump(output, sys.stdout, indent=4, sort_keys=True)
            elif args.format == "python":
                pprint.pprint(output)
            else:
                print("Unknown output format:", args.format, file=sys.stderr)
                return 1
        sys.stdout.write("\n")
        return 0
    finally:
        if args.filename != "-":
            f.close()


if __name__ == "__main__":
    sys.exit(main())
