from __future__ import print_function

import sys
import requests
import docopt

from . import slack, admin

USE_SLACK = False


def main():
    global USE_SLACK
    helpstr = """Report content of a Crunch Admin Page.

    Usage:
      %(script)s <urlpath> <contentkey> [--env=ENV] [--slack=CHANNEL] [--top=TOPCOUNT] [--key=KEY]...
      %(script)s (-h | --help)

    Arguments:
      urlpath                The admin page for which the report has to be sent.
      contentkey             The admin page response key to report.

    Options:
      -h --help              Show this screen
      --env=ENV              Environment against which to run the commands [default: eu]
      --slack=CHANNEL        Send messages to slack CHANNEL instead of writing it to stdout
      --top=TOPCOUNT         Number of entries to preview from the content [default: 10]
      -k=KEY --key=KEY       One ore more keys to report out of contentkey in preview.
    """ % dict(script=sys.argv[0])

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    env = arguments['--env']
    urlpath = arguments['<urlpath>']
    contentkey = arguments['<contentkey>']
    topcount = int(arguments["--top"])
    keys = arguments["--key"]
    USE_SLACK = arguments['--slack']

    hosts = admin.ENVIRONS[env]
    with admin.tunnel(hosts[0], 8081, 29081, hosts[1]) as connection:
        resp = requests.get(**admin.admin_url(connection, urlpath))
        if resp.status_code != 200:
            output("Failed to fetch %s for %s" % (urlpath, env))
            sys.exit(1)

        entries = resp.json()[contentkey]

        title = "AUTOMATIC REPORT OF {fqdn_link}".format(fqdn_link=admin.fqdn_link(env, urlpath))
        msgchunks = ["{count} entries currently in {contentkey}\n"
                     "".format(contentkey=contentkey, count=len(entries))]
        for idx, entry in enumerate(entries, 1):
          if idx > topcount:
            msgchunks.append("...")
            break
          reportedkeys = keys or entry.keys()
          msgchunks.append(" ".join(("%s=%s" % (k, entry.get(k)) for k in reportedkeys)))

        output(len(entries), title, "\n".join(msgchunks))


def output(marker, title, msg):
    if USE_SLACK:
        r = slack.message(channel=USE_SLACK, username="crunchbot",
                          icon_emoji=":exclamation:" if marker else ':grey_exclamation:' ,
                          attachments=[{
                              'title': title,
                              'text': msg
                          }])
        r.raise_for_status()
    else:
        print("\n".join((title, msg)))