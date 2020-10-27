import contextlib
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


@contextlib.contextmanager
def errors_to_slack(channel="app-status", username="crunchbot", icon_emoji=":cry:", **kwargs):
    '''Catch any errors that happen and send them to slack'''
    try:
        yield
    except Exception as e:
        print(e)
        kwargs['channel'] = channel
        kwargs['username'] = username
        kwargs['icon_emoji'] = icon_emoji
        if 'text' in kwargs:
            kwargs['text'] += ' "%s"' % e.message
        else:
            kwargs['text'] = e.message
        try:
            message(**kwargs)
        except Exception as e:
            print(e)
    finally:
        pass
