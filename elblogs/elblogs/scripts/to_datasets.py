# TODO:
# x Add time check to find_dot
# * Test reshape_datasets
# * Set up reshape cron job
# * Determine what to summarize for a dataset
# * Determine how to summarize across datasets
# * Determine how to integrate with app data (e.g. dataset size)
# * Automate the 500/504 weekly summary


import os
from os.path import basename
import sys

from docopt import docopt

from ..files import find_dot, logfile_to_datasets

def main():
    helpstr = """Prep all repos for dev

    Usage:
      %(script)s reset [<repo>] [--push] [--no-prompt] [--ipdb] [--verbose]
      %(script)s update [<repo>] [--push] [--no-prompt] [--ipdb] [--verbose]

    Options:
      -h --help                     Show this screen.
      --ipdb                        Dump to ipdb on command failure.

    """

    args = docopt(helpstr % dict(script=basename(sys.argv[0])))

    print 'Running with args:'
    print args

    use_ipdb = args['--ipdb']

    if use_ipdb:
        from ipdb import launch_ipdb_on_exception
        with launch_ipdb_on_exception():
            reshape_datasets(start, end, destination)
            return

    reshape_datasets(start, end, destination)

def reshape_datasets(start=None, end=None, destination="."):
    ''' Find log files, possibly for a time range, and copy their entries to
        files organized by dataset.
    '''
    files = find_dot(start, end)
    for f in files:
        logfile_to_datasets(f, destination)
    return
