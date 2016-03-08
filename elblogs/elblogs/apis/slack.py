import json

import requests

## See also a copy of this in pow.clang

def message(**kwargs):
    ''' Send a message to our Slack team

        kwargs:
        * `text` message
        * `channel` to post in
        * `username` to post as
        * `icon_emoji` to use for username
    '''
    u = "https://hooks.slack.com/services/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"
    if kwargs['channel'][0] not in ["#", "@"]:
        kwargs['channel'] = "#" + kwargs['channel']
    kwargs['parse'] = "full"
    payload = {"payload": json.dumps(kwargs)}
    r = requests.post(u, data=payload)
    return r
