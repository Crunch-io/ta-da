"""
Code used by multiple Simulated User Testing modules and scripts
"""
import six

from crunch_util import connect_pycrunch


def connect_api(config, args):
    """
    config: dict with contents of config.yaml
    args: dict with docopt options:
        -p: profile name
        -u: user alias
        -v: verbose flag
    """
    profile_name = args["-p"]
    user_alias = args["-u"]
    profile = config["profiles"][profile_name]
    connect_params = {"api_url": profile["api_url"]}
    connect_params.update(profile["users"][user_alias])
    return connect_pycrunch(connect_params, verbose=args["-v"])


def get_command_name(args):
    """Return the command name out of docopt-generated args, or None"""
    for key, value in six.iteritems(args):
        if key[:1] in ("-", "<"):
            continue
        if value:
            return key
    else:
        return None
