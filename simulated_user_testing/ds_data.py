#!/usr/bin/env python3
"""
Big Dataset data helper script

Usage:
    ds.meta list-datasets [options] [--projects] [--project=PROJECT]

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -i                      Run interactive prompt after executing command
    -v                      Print verbose messages
    --name=NAME             Override name in JSON file (post, addvar)
    --alias=ALIAS           Override alias in JSON file (addvar)
    -u --unique-subvar-aliases
                            Generate unique subvariable aliases (addvar)

Commands:
    list-datasets
        Print list of datasets (tests pycrunch connection)
"""
from __future__ import print_function
import sys

import docopt
import yaml
import six
from six.moves.urllib import parse as urllib_parse

from crunch_util import connect_pycrunch


def do_list_datasets(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    verbose = args["-v"]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    if args["-i"]:
        import IPython

        IPython.embed()
    if args["--projects"]:
        for proj in six.itervalues(site.projects.index):
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
        for ds_info in six.itervalues(datasets_index):
            print(u"{ds[id]} {ds[name]}".format(ds=ds_info))
        return 0
    for ds in six.itervalues(site.datasets.index):
        print(u"{ds.id} {ds.name}".format(ds=ds))
    return 0


def main():
    args = docopt.docopt(__doc__)
    if args["list-datasets"]:
        return do_list_datasets(args)
    else:
        raise NotImplementedError("Sorry, that command is not yet implemented.")


if __name__ == "__main__":
    sys.exit(main())
