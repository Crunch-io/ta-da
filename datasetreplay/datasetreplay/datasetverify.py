from __future__ import print_function

import json
import sys
import time

import datetime
import requests
import docopt
from .datasetreplay import ENVIRONS, tunnel, admin_url


def main():
    helpstr = """Test Integrity of a dataset.

    Usage:
      %(script)s <dsid> [--env=ENV] [--tracefile=TRACEFILE]
      %(script)s (-h | --help)

    Arguments:
      dsid ID of the dataset that should be tested

    Options:
      -h --help               Show this screen
      --env=ENV               Environment against which to run the commands [default: eu]
      --tracefile=TRACEFILE   Save test logs to a file.
    """ % dict(
        script=sys.argv[0]
    )

    arguments = docopt.docopt(helpstr, sys.argv[1:])
    dataset_id = arguments["<dsid>"]
    env = arguments["--env"]
    tracefile = arguments["--tracefile"]

    hosts = ENVIRONS[env]

    dataset_info = _fetch_dataset_info(hosts, dataset_id)
    if dataset_info is None:
        # Crunch is broken or dataset was an autoreplay.
        return

    dataset_integrity = dataset_info["verify_integrity"]
    if dataset_info.get("datamap"):
        # The datamap is corrupted
        dataset_integrity = False

    if dataset_integrity is None:
        # Never had a transaction committed
        return

    dataset = dataset_info["dataset"]
    if dataset_integrity is False:
        notify(
            dataset_id,
            dataset["name"],
            "Broken: %s - %s - %s"
            % (
                dataset_info.get("last_transaction"),
                dataset_info.get("last_action"),
                dataset_info.get("datamap") and len(dataset_info.get("datamap")),
            ),
            success=False,
            tracefile=tracefile,
        )
    elif dataset_integrity is True:
        notify(dataset_id, dataset["name"], "OK", success=True, tracefile=tracefile)
    else:
        notify(
            dataset_id,
            dataset["name"],
            "Unexpected State!",
            success=False,
            tracefile=tracefile,
        )


def notify(
    dataset_id, dataset_name, message, success=True, skipped=False, tracefile=None
):
    print(message)

    if tracefile is not None:
        with open(tracefile, "a") as f:
            f.write(
                json.dumps(
                    {
                        "date": datetime.datetime.utcnow().strftime("%Y%m%d"),
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "success": success,
                        "skipped": skipped,
                        "message": message,
                        "format": "%(dataset_id)s: %(message)s",
                    }
                )
                + "\n"
            )


def _fetch_dataset_info(hosts, dataset_id):
    for _attempts in range(30):
        # Retry for up to 30 minutes (60*30 seconds) to avoid race conditions,
        # as we don't want to block the dataset to verify integrity
        # and thus dataset might be changing while we verify it.
        with tunnel(hosts[0], 8081, 29081, hosts[1]) as connection:
            print("Fetching Dataset info for %s" % dataset_id)
            resp = requests.get(**admin_url(connection, "/datasets/%s/" % dataset_id))
            if resp.status_code != 200:
                print("ERROR: %s" % resp.text)
                return None

            dataset_info = resp.json()
            dataset = dataset_info["dataset"]
            if dataset["name"].startswith("AUTOREPLAY "):
                # We don't want to verify our own replays
                print("SKIPPED: %s was a replay" % dataset["name"])
                return None

            dataset_integrity = dataset_info["verify_integrity"]
            if dataset_integrity is not False:
                return dataset_info

        # wait 30 seconds between each retry
        time.sleep(30)
    else:
        # Retries exhausted, just return last dataset info.
        return dataset_info
