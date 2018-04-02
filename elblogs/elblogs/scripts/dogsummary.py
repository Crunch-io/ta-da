import json
import os
from os.path import basename
import sys

from docopt import docopt

from ..apis import ddog as dog
from ..apis.slack import errors_to_slack, message
from ..dates import start_and_end, date_range_label, date_to_dogtime

def main():
    helpstr = """Summarize ELB logs in a given range

    Usage:
      %(script)s [<days>] [<before_date>] [--ipdb] [--slack]

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
    days = int(args.get('<days>') or 1)
    before_date = args['<before_date>']

    start_date, end_date = start_and_end(before_date, days)
    daterange = date_range_label(start_date, end_date)
    start, end = date_to_dogtime(start_date, end_date)

    print daterange
    print "start", start
    print "end", end

    if use_ipdb:
        from ipdb import launch_ipdb_on_exception
        with launch_ipdb_on_exception():
            summary = dog_summary_stats(start, end)
    elif send_to_slack:
        with errors_to_slack(channel="systems", text="Oops! Error running dog.summary on ahsoka:"):
            summary = dog_summary_stats(start, end)
    else:
        summary = dog_summary_stats(start, end)

    if send_to_slack:
        ## Send the output there too!
        body, icon_emoji = slackify_dog_summary(summary, daterange)
        r = message(channel="systems", username="crunchbot",
            icon_emoji=icon_emoji, attachments=body)
        r.raise_for_status()
    else:
        print summary

    return

def dog_summary_stats(start, end):
    ## Appends:
    append_good = dog.count_zz9("import_frame", start, end, status="success")
    append_bad = dog.count_zz9("import_frame", start, end, status="failed")
    append_invalid = dog.count_zz9("import_frame", start, end, status="invalid")
    append_total = append_good + append_bad

    ## Merges:
    merge_total = dog.count_cr("datasetactionscatalog", start, end, method="POST")
    merge_bad = dog.count_task("play_workflow", start, end, status="failed")
    merge_good = dog.count_task("play_workflow", start, end, status="success")
    ## Note that if good + bad != total, something is up

    ## Query Timeouts:
    qt_total = dog.count("zz9.client.timeouts", start, end,
        scope="region:eu-west-1")

    return {
        "append": {
            "total": append_total,
            "good": append_good,
            "bad": append_bad,
            "invalid": append_invalid
        },
        "merge": {
            "total": merge_total,
            "good": merge_good,
            "bad": merge_bad
        },
        "timeout": {
            "total": qt_total,
        },
    }

def slackify_dog_summary(summary, daterange):
    if summary['append']['bad'] + summary['merge']['bad'] == 0:
        color = "good"
        icon_emoji = ":grinning:"
    else:
        color = "warning"
        icon_emoji = ":worried:"
    query_timeouts = summary.pop("timeout")
    print(summary)
    body = [{
        "title": "Query summary for %s" % (daterange),
        "fallback": "Query summary: "+ color,
        "fields": [
            {
                "title": "%ss: failed/total (%% success)" % k,
                "value": "%s/%s (%s%%)" % (v['bad'], v['total'], round(100*v['good']/v['total']) if v['total'] else "-"),
                "short": True
            }
            for k, v in summary.iteritems()],
        "color": color
    }]

    body[0]["fields"] += [{
        ## Add in the query timeouts, which don't follow that pattern
        "title": "ZZ9 Query Timeouts",
        "value": query_timeouts["total"],
        "short": True
    }, {
        ## Also, let's make an extra one for the "invalid" appends
        "title": "'Invalid' Appends (user error)",
        "value": summary['append']['invalid'],
        "short": True
    }]
    return body, icon_emoji
