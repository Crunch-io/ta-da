# TODO:
# x Add time check to find_dot
# x Test reshape_datasets
# x Set up reshape cron job
    # 30 * * * * $HOME/tools/elblogs/venv/bin/elb.ds /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/ /var/www/logs/AWSLogs/910774676937/by_dataset >> $HOME/elbds.out 2>&1
# * Determine what to summarize for a dataset
# * Determine how to summarize across datasets
# * Determine how to integrate with app data (e.g. dataset size)
# * Automate the 500/504 weekly summary
# * Make daily 504 report to slack

from datetime import datetime
import os
from os.path import basename
import sys

from docopt import docopt

from ..files import find_dot, logfile_to_datasets

def main():
    helpstr = """Split and combine logfiles by dataset id

    Usage:
      %(script)s [<source>] [<dest>] [<start>] [<end>] [--ipdb]

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
            out = reshape_datasets(start, end, dest, source_dir)
            return

    out = reshape_datasets(start, end, dest, source_dir)

    return

def reshape_datasets(start=None, end=None, destination="..", source_dir="."):
    ''' Find log files, possibly for a time range, and copy their entries to
        files organized by dataset.
    '''
    files = find_dot(start, end, path=source_dir)
    out = logfile_to_datasets(files, destination)
    return out
