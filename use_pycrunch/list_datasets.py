#!/usr/bin/env python3
"""
Print dataset IDs and names

Usage:
    {program} [options]

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -u USER_NAME            User section in config [default: default]
    -v                      Print verbose messages
    -i                      Interactive exploration
    --projects              List projects, not datasets
    --personal              List personal items
    --project=PROJECTID     List items in a project
"""
from __future__ import print_function
import logging
import os
import sys

import docopt
import six
from six.moves.urllib import parse as urllib_parse
import yaml

from crunch_util import connect_pycrunch, connection_info_from_config


def main():
    args = docopt.docopt(__doc__.format(program=os.path.basename(sys.argv[0])))
    logging.basicConfig(level=logging.INFO)

    config_filename = args["-c"]
    verbose = args["-v"]
    with open(config_filename) as f:
        config = yaml.safe_load(f)
    connection_info = connection_info_from_config(config, args)

    site = connect_pycrunch(connection_info, verbose=verbose)

    if args["-i"]:
        # Launch ipython REPL
        import IPython

        IPython.embed()

    if args["--projects"] and not args["--personal"] and not args["--project"]:
        catalog = site.session.get(site.catalogs.projects).payload
        for proj_url, proj in six.iteritems(catalog.index):
            print(u"{proj.id} {proj.name}".format(proj=proj))

    elif args["--personal"]:
        personal_projects_url = site.catalogs.projects + "personal/"
        catalog = site.session.get(personal_projects_url).payload
        for item_url, item in six.iteritems(catalog.index):
            if item.type == 'dataset' and args["--projects"]:
                continue
            elif item.type != 'dataset' and not args["--projects"]:
                continue
            print(u"{item.id} {item.name}".format(item=item))

    elif args["--project"]:
        project_id = args["--project"]
        project_url = "{}{}/".format(site.catalogs.projects, project_id)
        catalog = site.session.get(project_url).payload
        for item_url, item in six.iteritems(catalog.index):
            if item.type == 'dataset' and args["--projects"]:
                continue
            elif item.type != 'dataset' and not args["--projects"]:
                continue
            print(u"{item.id} {item.name}".format(item=item))

    else:
        for ds_url, ds in six.iteritems(site.datasets.index):
            print(u"{ds.id} {ds.name}".format(ds=ds))

    return 0


if __name__ == "__main__":
    sys.exit(main())
