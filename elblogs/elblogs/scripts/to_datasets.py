from datetime import datetime
import os
from os.path import basename
import sys

from docopt import docopt

from ..files import find_dot, logfile_to_datasets
from ..apis.slack import errors_to_slack

def main():
    helpstr = """Split and combine logfiles by dataset id

    Usage:
      %(script)s [<source>] [<dest>] [<start>] [<end>] [--ipdb] [--slack]

    Options:
      -h --help                     Show this screen.
      --ipdb                        Dump to ipdb on command failure.
      --slack                       Send error messages to slack
    """

    args = docopt(helpstr % dict(script=basename(sys.argv[0])))

    print 'Running with args:'
    print args

    use_ipdb = args['--ipdb']
    send_to_slack = args['--slack']
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
    elif send_to_slack:
        with errors_to_slack(channel="systems", text="Oops! Error running elb.ds on ahsoka:"):
            out = reshape_datasets(start, end, dest, source_dir)
    else:
        out = reshape_datasets(start, end, dest, source_dir)
    return

def reshape_datasets(start=None, end=None, destination="..", source_dir="."):
    ''' Find log files, possibly for a time range, and copy their entries to
        files organized by dataset.
    '''
    files = find_dot(start, end, path=source_dir)
    out = logfile_to_datasets(files, destination)
    return out
