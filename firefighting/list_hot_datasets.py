#!/var/lib/crunch.io/venv/bin/python
"""
Print a list of all of the dataset IDs in ``host_map`` for a given host.

Usage:
    list_hot_datasets.py [options] <zz9-host-ip-addr>

Options:
    --cr-lib-config=FILENAME  [default: /var/lib/crunch.io/cr.server-0.conf]
    --leased                  Only list datasets currently leased
    --force-clear             Remove the entries from lease map and host_map
    --yes                     Assume "Are you sure?" answer is yes

Run this on a backend server. The datasets listed are those who are either currently
leased or had most recently been leased on that ZZ9 host. Only pass --force-clear
if you *know* that the ZZ9 host no longer exists. You will be asked "Are you sure?"
"""
from __future__ import print_function
import os
import sys

import docopt
from magicbus import bus
from magicbus.plugins import loggers
import six

from cr.lib.commands.common import load_settings, startup
from cr.lib.loglib import log_to_stdout
from cr.lib.settings import settings
from cr.lib import stores
from zz9lib.net import get_factory_info_from_url


def _cr_lib_init(args):
    """
    Run this before doing anything with cr.lib
    """
    settings_yaml = args["--cr-lib-config"]
    settings.update(load_settings(settings_yaml))
    startup()


def list_leased(host):
    result = []
    lease_map = stores.stores.zz9.map
    for dataset_id in lease_map.scan_iter():
        if dataset_id.startswith("__"):
            continue
        factory_url = lease_map.get(dataset_id)
        if not factory_url:
            continue
        factory_info = get_factory_info_from_url(factory_url)
        if factory_info["host"] != host:
            continue
        result.append(dataset_id)
    return result


def list_hot(host):
    result = []
    host_map = stores.stores.zz9.host_map
    for dataset_id in host_map.scan_iter():
        if dataset_id.startswith("__"):
            continue
        if host_map.get(dataset_id) != host:
            continue
        result.append(dataset_id)
    return result


def force_clear(host, answer_yes=False):
    dataset_ids = list_hot(host)
    if answer_yes:
        print(
            "Removing {} datasets from lease map and host map pointing to host {}".format(
                len(dataset_ids), host
            )
        )
    else:
        answer = six.moves.input(
            "Remove {} datasets from lease map and host map pointing to host {}?".format(
                len(dataset_ids), host
            )
        )
        if not answer.strip().lower().startswith("y"):
            print("Canceled.")
            return 1
    lease_map = stores.stores.zz9.map
    host_map = stores.stores.zz9.host_map
    for dataset_id in dataset_ids:
        # FYI, deleting a non-existent key from redis does not raise an exception,
        # so we don't need to guard against something else also removing keys.
        del lease_map[dataset_id]
        del host_map[dataset_id]
    return 0


def main():
    args = docopt.docopt(__doc__)
    level = int(os.environ.get("CR_LOGLEVEL", "30"))
    loggers.StdoutLogger(bus, format="%(message)s\n", level=level).subscribe()
    log_to_stdout(level=30)
    _cr_lib_init(args)

    host = args["<zz9-host-ip-addr>"]

    if args["--force-clear"]:
        return force_clear(host, answer_yes=args["--yes"])

    if args["--leased"]:
        # Print IDs of datasets leased on this host
        for dataset_id in list_leased(host):
            print(dataset_id)
        return

    # Print IDs of datasets "hot" on this host
    for dataset_id in list_hot(host):
        print(dataset_id)


if __name__ == "__main__":
    sys.exit(main())