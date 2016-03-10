from datetime import datetime
import os
from os.path import basename
import sys

from docopt import docopt

from ..files import find_dot
from ..analyze import analyze_log, summarize


def main():
    helpstr = """Summarize ELB logs in a given range

    Usage:
      %(script)s [<source>] [<start>] [<end>] [--ipdb]

    Options:
      -h --help                     Show this screen.
      --ipdb                        Dump to ipdb on command failure.

    """

    args = docopt(helpstr % dict(script=basename(sys.argv[0])))

    print 'Running with args:'
    print args

    use_ipdb = args['--ipdb']
    source_dir = args.get('<source>', ".")
    dest = args.get('<dest>', "..")
    start = args['<start>']
    end = args['<end>']

    if not start:
        start = datetime.strftime(datetime.fromtimestamp(os.path.getmtime(dest)),
            "%Y%m%dT%H%M")

    if use_ipdb:
        from ipdb import launch_ipdb_on_exception
        with launch_ipdb_on_exception():
            out = reshape_datasets(start, end, dest)
            return

    out = reshape_datasets(start, end, dest)

    return



def elb_summary_stats(start=None, end=None):
    ''' Find log files, possibly for a time range, read them, and return the
        indicated quantities for all.
    '''
    files = find_dot(start, end)
    results = {}
    for f in files:
        results[f] = analyze_log(load_log(f))
    return summarize(results)
