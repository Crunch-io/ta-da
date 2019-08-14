from __future__ import print_function

import json
import sys
import docopt
import logging
from . import slack

log = logging.getLogger(__name__)

USE_SLACK = False


def notify(title, date, success, text, ratio, skipped, skiptext):
    skiptitle = '%s Skips for %s (%s)' % (title, date, skipped)
    title = '%s for %s (%s/%s)' % (title, date, ratio[0], ratio[1])
    if USE_SLACK:
        message_parts = [{'title': title,
                          'text': 'ALL SUCCESSFUL' if success else '```%s```' % text,
                          "mrkdwn_in": ["text"]}]
        if skipped:
            message_parts.append({
                'title': skiptitle,
                'text': '```%s```' % skiptext,
                "mrkdwn_in": ["text"]
            })
        r = slack.message(channel=USE_SLACK, username="crunchbot",
                          icon_emoji=":grinning:" if success else ':worried:',
                          attachments=message_parts)
        r.raise_for_status()
    else:
        print(title)
        print(text)
        print(skiptitle)
        print(skiptext)


def main():
    global USE_SLACK
    helpstr = """Report a tracefile content from a specific day

    Usage:
      %(script)s <tracefile> <date> <title> [--slack=CHANNEL] [--failures]
      %(script)s (-h | --help)

    Arguments:
      tracefile The path of the file where the tracing was saved.
      date      The date for which content should be reported
      title     Title of the report

    Options:
      -h --help               Show this screen
      --slack=CHANNEL         Send the output to slack channel
      --failures              Only report failures and skips
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    tracefile = arguments['<tracefile>']
    date = arguments['<date>']
    title = arguments['<title>']
    USE_SLACK = arguments['--slack']
    failures_only = arguments['--failures']

    total = 0
    failures = 0
    skipped = 0

    skiplines = []
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
                if logline.get('skipped', False):
                    skipped += 1
                    skiplines.append(logline['format'] % logline)
                    continue

                total += 1
                if not logline['success']:
                    failures += 1
                if failures_only and logline['success']:
                    continue
                loglines.append(logline['format'] % logline)

    notify(title, date, failures == 0, '\n'.join(loglines),
           (total-failures, total), skipped, '\n'.join(skiplines))



