from __future__ import print_function

import json
import sys
import docopt
import logging
from . import slack

log = logging.getLogger(__name__)

USE_SLACK = False


def notify(title, date, success, text, ratio):
    title = '%s for %s (%s/%s)' % (title, date, ratio[0], ratio[1])
    if USE_SLACK:
        r = slack.message(channel="api", username="crunchbot",
                          icon_emoji=":grinning:" if success else ':worried:',
                          attachments=[{'title': title,
                                        'text': '```%s```' % text,
                                        "mrkdwn_in": ["text"]}])
        r.raise_for_status()
    else:
        print(title)
        print(text)


def main():
    global USE_SLACK
    helpstr = """Report a tracefile content from a specific day

    Usage:
      %(script)s <tracefile> <date> <title> [--slack] [--failures]
      %(script)s (-h | --help)

    Arguments:
      tracefile The path of the file where the tracing was saved.
      date      The date for which content should be reported
      title     Title of the report

    Options:
      -h --help               Show this screen
      --slack                 Send the output to slack
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    tracefile = arguments['<tracefile>']
    date = arguments['<date>']
    title = arguments['<title>']
    USE_SLACK = arguments['--slack']
    failures_only = arguments['--failures']

    total = 0
    failures = 0
    loglines = []
    with open(tracefile, 'r') as f:
        for l in f:
            try:
                logline = json.loads(l)
            except ValueError:
                log.exception('Invalid line: %s', l)
                # Spurious line???
                pass

            if date == logline['date']:
                total += 1
                if not logline['success']:
                    failures += 1
                if failures_only and logline['success']:
                    continue
                loglines.append(logline['format'] % logline)

    notify(title, date, failures == 0, '\n'.join(loglines),
           (total-failures, total))



