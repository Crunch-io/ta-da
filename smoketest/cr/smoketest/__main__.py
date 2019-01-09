"""
Crunch Smoke Test Suite

Usage:
    cr.smoketest [options] pick-random-dataset [--zz9repo=REPODIR]
    cr.smoketest [options] append-random-rows <dataset-id>
    cr.smoketest [options] get-metadata <dataset-id> [<output-filename>]
    cr.smoketest [options] list-datasets
    cr.smoketest [options] stress

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -v                      Print verbose messages
    -i                      Start ipython after some commands
    --projects              List projects, not datasets
    --project=PROJNAME      List datasets in a project
    --sparse-data           Make > 80% of new values system missing
    --num-rows=NUMROWS      [default: 10]
    --zz9repo=REPODIR       [default: /var/lib/crunch.io/zz9repo]
    --num-threads=N         [default: 1]
    --idle-timeout=N        Seconds to wait for dataset release [default: 120]
    --cleaner-delay=N       Seconds to wait for cleaner loop [default: 180]
    --skip-cleanup          Don't delete test datasets on exit

Commands:
    pick-random-dataset
        Look at the zz9repo dir, print random datasetID
    append-random-rows
        Read a dataset variable definitions, generate compatible CSV rows,
        append those rows to the dataset.
    get-metadata
        Query dataset metadata and save it in JSON format
    stress:
        Run in a loop creating, updating, and deleting datasets
"""
from __future__ import print_function
import json
import os
import random
import sys

import docopt
import six
from six.moves.urllib import parse as urllib_parse
import yaml

from .crunch_util import (
    append_csv_file_to_dataset,
    connect_pycrunch,
    get_ds_metadata,
    get_pk_alias,
)
from .gen_data import open_csv_tempfile, write_random_rows
from .stress import run_stress_loop

this_module = sys.modules[__name__]


###########################
# Helper functions


def load_config(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    return config


def pick_random_dataset(zz9repo="/var/lib/crunch.io/zz9repo"):
    prefix_dirs = os.listdir(zz9repo)
    while prefix_dirs:
        prefix = random.choice(prefix_dirs)
        prefix_dirs.remove(prefix)
        dataset_dirs = os.listdir(os.path.join(zz9repo, prefix))
        if dataset_dirs:
            return random.choice(dataset_dirs)
    raise Exception("No datasets to choose from.")


###########################
# Command functions


def do_pick_random_dataset(args):
    zz9repo = args["--zz9repo"]
    print(pick_random_dataset(zz9repo))


def do_get_metadata(args):
    config = load_config(args)
    site = connect_pycrunch(config["connection"], verbose=args["-v"])
    ds_id = args["<dataset-id>"]
    ds = site.datasets.by("id")[ds_id].entity
    metadata = get_ds_metadata(ds)
    if not args["<output-filename>"]:
        out = sys.stdout
    else:
        out = open(args["<output-filename>"], "w")
    try:
        json.dump(metadata, out, indent=4, sort_keys=True)
        out.write("\n")
    finally:
        if args["<output-filename>"]:
            out.close()
    if args["-i"]:
        import IPython

        IPython.embed()


def do_append_random_rows(args):
    config = load_config(args)
    site = connect_pycrunch(config["connection"], verbose=args["-v"])
    ds_id = args["<dataset-id>"]
    ds = site.datasets.by("id")[ds_id].entity
    metadata = get_ds_metadata(ds)
    var_defs = metadata["body"]["table"]["metadata"]
    pk = get_pk_alias(ds)
    num_rows = int(args["--num-rows"])
    with open_csv_tempfile() as f:
        write_random_rows(var_defs, pk, num_rows, f, sparse_data=args["--sparse-data"])
        f.seek(0)
        append_csv_file_to_dataset(site, ds, f, verbose=args["-v"])


def do_list_datasets(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    verbose = args["-v"]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    if args["-i"]:
        import IPython

        IPython.embed()
    if args["--projects"]:
        for proj_url, proj in six.iteritems(site.projects.index):
            print(u"{proj.id} {proj.name}".format(proj=proj))
        return 0
    if args["--project"]:
        proj_name_or_id = args["--project"]
        try:
            proj = site.projects.by("id")[proj_name_or_id]
        except KeyError:
            proj = site.projects.by("name")[proj_name_or_id]
        url = urllib_parse.urljoin(proj.entity_url, "datasets/")
        response = site.session.get(url)
        datasets_index = response.json()["index"]
        for ds_url, ds_info in six.iteritems(datasets_index):
            print(u"{ds[id]} {ds[name]}".format(ds=ds_info))
        return 0
    for ds_url, ds in six.iteritems(site.datasets.index):
        print(u"{ds.id} {ds.name}".format(ds=ds))
    return 0


def do_stress(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    num_threads = int(args["--num-threads"])
    idle_timeout = int(args["--idle-timeout"])
    cleaner_delay = int(args["--cleaner-delay"])
    num_rows = int(args["--num-rows"])
    assert num_threads >= 1
    run_stress_loop(
        config,
        num_threads=num_threads,
        verbose=args["-v"],
        idle_timeout=idle_timeout,
        cleaner_delay=cleaner_delay,
        sparse_data=args["--sparse-data"],
        num_rows=num_rows,
        do_cleanup=(not args["--skip-cleanup"]),
    )


def main():
    args = docopt.docopt(__doc__)
    for key, value in six.iteritems(args):
        if not key[:1] in ("-", "<") and value:
            command_name = key.lower().replace("-", "_")
            command_func = getattr(this_module, "do_" + command_name, None)
            if command_func:
                return command_func(args)
            raise ValueError("Invalid subcommand: {}".format(command_name))
    raise ValueError("Invalid or missing subcommand.")


if __name__ == "__main__":
    main()
