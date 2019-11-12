import json
import os
from os.path import basename
import sys

from docopt import docopt

from ..analyze import analyze_log, summarize, format_summary
from ..apis.slack import errors_to_slack, message
from ..dates import start_and_end, date_range_label
from ..files import find_dot, load_log, get_error_entries


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

    start_date, end_date = start_and_end(before_date, days)
    daterange = date_range_label(start_date, end_date)

    start = start_date.strftime("%Y%m%d")
    end = end_date.strftime("%Y%m%d")

    print "start", start
    print "end", end

    if use_ipdb:
        from ipdb import launch_ipdb_on_exception
        with launch_ipdb_on_exception():
            summary, errors = elb_summary_stats(start, end, source_dir)
    elif send_to_slack:
        with errors_to_slack(channel="app-status", text="Oops! Error running elb.summary on ahsoka:"):
            summary, errors = elb_summary_stats(start, end, source_dir)
    else:
        summary, errors = elb_summary_stats(start, end, source_dir)

    if send_to_slack:
        ## Send the output there too!
        if summary['sum_reqs'] == 0:
            message(channel="app-status", username="crunchbot", icon_emoji=":interrobang:",
                text="@npr: elb.summary reports no requests for %s" % (daterange))
        else:
            if summary['pct_500s'] < 0.001:
                ## Five nines!
                color = "good"
                if summary['sum_500s'] == 0:
                    icon_emoji = ":parrot:"
                else:
                    icon_emoji = ":sunglasses:"
            elif summary['pct_500s'] < 0.01:
                ## Four nines
                color = "good"
                icon_emoji = ":simple_smile:"
            elif summary['pct_500s'] < 0.1:
                ## Three nines
                color = "warning"
                icon_emoji = ":worried:"
            else:
                color = "danger"
                icon_emoji = ":scream_cat:"
            body = [{
                "title": "ELB summary for %s" % (daterange),
                "fallback": "ELB summary: "+ color,
                "fields": [{"title": k, "value": v, "short": True}
                    for k, v in format_summary(summary).iteritems()],
                "color": color
            }]
            if len(errors):
                body += [{
                    "title": "502s, 503s, and 504s",
                    "text": ''.join(errors),
                    "fallback": "Log entries for >500 status requests",
                    "color": color
                }]
            r = message(channel="app-status", username="crunchbot",
                icon_emoji=icon_emoji, attachments=body)
            r.raise_for_status()
    else:
        print summary

    return


def elb_summary_stats(start=None, end=None, path="."):
    ''' Find log files, possibly for a time range, read them, and return the
        indicated quantities for all.
    '''
    files = find_dot(start, end, path=path)
    results = {}
    errs = []
    for f in files:
        results[f] = analyze_log(load_log(f))
        errs += get_error_entries(f)
    return summarize(results), errs
