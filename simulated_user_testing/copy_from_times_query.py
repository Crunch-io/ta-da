#!/var/lib/crunch.io/venv/bin/python
r"""
Print the Dataset.copy_from times for a series of datasets

Queries the Mongo database directly. Output goes to stdout in CSV format.

Usage:
    copy_from_times.py [options]

Options:
    --config=FILENAME   [default: /var/lib/crunch.io/cr.server-0.conf]
    --limit=LIMIT       [default: 52] Max. number of output data points
    --name=PATTERN      Dataset name search regex
                        [default: ^Profiles USA 20\d\d-\d\d-\d\d$]
"""
from __future__ import print_function
import csv
import sys

import docopt
import pymongo
import yaml


def main():
    args = docopt.docopt(__doc__)
    config_filename = args["--config"]
    limit = int(args["--limit"])
    with open(config_filename) as f:
        config = yaml.safe_load(f)
    mongo_url = config["APP_STORE"]["URL"]
    client = pymongo.MongoClient(mongo_url)
    db = client.get_default_database()
    filter_expr = {
        "name": {"$regex": args["--name"]},
        "version": "master__tip",
        "cached_fields.rows": {"$gt": 0},
    }
    result = db.datasets.find(
        filter_expr,
        projection={
            "_id": False,
            "cached_fields": True,
            "creation_time": True,
            "crunch_id": True,
            "name": True,
        },
        limit=limit,
        sort=[("creation_time", pymongo.DESCENDING)],
    )
    datasets = list(result)
    datasets.reverse()
    writer = csv.writer(sys.stdout)
    writer.writerow(["dataset_id", "dataset_name", "creation_time", "copy_from_timing"])
    for dataset in datasets:
        action = find_first_copy_from_action(db, dataset)
        if action is None:
            continue
        writer.writerow(
            [
                dataset["crunch_id"],
                dataset["name"],
                dataset["creation_time"],
                action["timing"],
            ]
        )


def find_first_copy_from_action(db, dataset):
    filter_expr = {"dataset_id": dataset["crunch_id"], "key": "Dataset.copy_from"}
    result = db.actions.find(
        filter_expr,
        projection={
            "_id": False,
            "dataset_id": True,
            "hash": True,
            "key": True,
            "timing": True,
            "utc": True,
        },
        limit=1,
        sort=[("utc", pymongo.DESCENDING)],
    )
    result = list(result)
    if not result:
        return None
    return result[0]


if __name__ == "__main__":
    sys.exit(main())
