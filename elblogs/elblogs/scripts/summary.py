from datetime import datetime, timedelta
import json
import os
from os.path import basename
import sys

from docopt import docopt

from ..files import find_dot, load_log
from ..analyze import analyze_log, summarize
from ..apis.slack import errors_to_slack, message


def main():
    helpstr = """Summarize ELB logs in a given range

    Usage:
      %(script)s [<source>] [<days>] [<before_date>] [--ipdb] [--slack]

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
    days = int(args.get('<days>', 1))
    before_date = args['<before_date>']

    if before_date:
        before_date = datetime.strptime(before_date, "%Y%m%d")
    else:
        before_date = datetime.utcnow()

    start = datetime.strftime(before_date - timedelta(days=days),"%Y%m%d")
    end = datetime.strftime(before_date - timedelta(days=1),"%Y%m%d")

    print "start", start
    print "end", end

    if use_ipdb:
        from ipdb import launch_ipdb_on_exception
        with launch_ipdb_on_exception():
            out = elb_summary_stats(start, end, source_dir)
    elif send_to_slack:
        with errors_to_slack(channel="systems", text="Oops! Error running elb.summary on ahsoka:"):
            out = elb_summary_stats(start, end, source_dir)
    else:
        out = elb_summary_stats(start, end, source_dir)

    if send_to_slack:
        ## Send the output there too!
        if out['sum_reqs'] == 0:
            message(channel="systems", username="crunchbot", icon_emoji=":interrobang:",
                text="@npr: elb.summary reports no requests in the %s day(s) prior to %s" % (days, before_date))
        else:
            if out['pct_500s'] < 0.01:
                ## Four nines
                color = "good"
                icon_emoji = ":grinning:"
            elif out['pct_500s'] < 0.1:
                ## Three nines
                color = "warning"
                icon_emoji = ":worried:"
            else:
                color = "danger"
                icon_emoji = ":scream_cat:"
            body = {
                "text": "ELB summary for the %s day(s) prior to %s" % (days, before_date),
                "fallback": "ELB summary: "+ color,
                "fields": [{"title": k, "value": v, "short": True} for k, v in out.iteritems()],
                "color": color
            }
            r = message(attachments=[body])
            print r.raise_for_status()
    else:
        print out

    return


def elb_summary_stats(start=None, end=None, path="."):
    ''' Find log files, possibly for a time range, read them, and return the
        indicated quantities for all.
    '''
    files = find_dot(start, end)
    results = {}
    for f in files:
        results[f] = analyze_log(load_log(f))
    return summarize(results)
