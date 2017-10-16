from __future__ import print_function

import json
import sys
import docopt
from . import slack

USE_SLACK = False


def notify(date, success, text):
    if USE_SLACK:
        r = slack.message(channel="api", username="crunchbot",
                          icon_emoji=":grinning:" if success else ':worried:',
                          attachments=[{'title': 'Dataset Replay Report fo %s' % date,
                                        'text': '```%s```' % text,
                                        "mrkdwn_in": ["text"]}])
        r.raise_for_status()
    else:
        print('Dataset Replay Report fo %s' % date)
        print(text)


def main():
    global USE_SLACK
    helpstr = """Report a tracefile content from a specific day

    Usage:
      %(script)s <tracefile> <date> [--slack]
      %(script)s (-h | --help)

    Arguments:
      tracefile The path of the file where the tracing was saved.
      date      The date for which content should be reported

    Options:
      -h --help               Show this screen
      --slack                 Send the output to slack
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    tracefile = arguments['<tracefile>']
    date = arguments['<date>']
    USE_SLACK = arguments['--slack']

    failures = False
    loglines = []
    with open(tracefile, 'r') as f:
        for l in f:
            logline = json.loads(l)
            if date == logline['date']:
                if not logline['success']:
                    failures = True
                loglines.append(logline['format'] % logline)

    notify(date, not failures, '\n'.join(loglines))



