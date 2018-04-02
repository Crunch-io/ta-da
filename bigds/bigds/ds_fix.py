"""
Helper script for finding and doing stuff with broken datasets

Usage:
    ds.fix dostuff
"""
from __future__ import print_function
import sys
import time

import docopt


def do_stuff(args):
    print("Here I am")


def main():
    args = docopt.docopt(__doc__)
    t0 = time.time()
    try:
        if args["dostuff"]:
            return do_stuff(args)
        print("No command given.", file=sys.stderr)
        return 1
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main())

