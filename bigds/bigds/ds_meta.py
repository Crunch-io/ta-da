"""
Big Dataset metadata helper script

Usage:
    ds.meta get [options] <ds-id> <filename>
    ds.meta info [options] <filename>
    ds.meta anonymize [options] <filename>
    ds.meta post [options] <filename>

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -i                      Run interactive prompt after executing command
    -v                      Print verbose messages

Commands:
    get
        Download dataset metadata and save in JSON file
    info
        Print stats about metadata in JSON file
    anonymize
        Convert names and aliases in metadata to anonymized unique strings of
        the same length. Modifies file IN PLACE.
    post
        Create an empty dataset with metadata from JSON file

Example config.yaml file:
    local:
        connection:
            username: 'captain@crunch.io'
            password: 'asdfasdf'
            api_url: 'https://local.crunch.io:8443/api'
            verify: false
"""
from __future__ import print_function
from collections import defaultdict
import json
import sys
import time

import docopt
import yaml
import six

from .crunch_util import connect_pycrunch


def make_cats_key(categories_list, remove_ids=True):
    if remove_ids:
        categories_list = [d.copy() for d in categories_list]
        for d in categories_list:
            d.pop('id', None)
    return tuple(
        json.dumps(d, sort_keys=True)
        for d in categories_list)


class MetadataModel(object):

    def __init__(self, verbose=False):
        self.verbose = verbose
        self._meta = {}

    def get(self, site, ds_id):
        """
        Download dataset metadata into an internal data structure
        site: Crunch API object returned by connect_pycrunch
        ds_id: Dataset ID
        """
        if self.verbose:
            print("Downloading metadata for dataset", ds_id, end='')
        self._meta.clear()
        self._meta['id'] = ds_id
        ds_url = "{}{}/".format(site.datasets['self'], ds_id)
        response = site.session.get(ds_url)
        ds_info = response.payload
        self._meta['name'] = ds_info['body']['name']
        self._meta['description'] = ds_info['body']['description']
        self._meta['size'] = ds_info['body']['size']
        # Get variables
        if self.verbose:
            print(".", end='')
        variables_url = "{}/variables/".format(ds_url)
        response = site.session.get(variables_url)
        variables_info = response.payload
        self._meta['variables'] = variables = {}
        variables['index'] = variables_info['index']
        # Get weights
        if self.verbose:
            print(".", end='')
        weights_url = "{}/variables/weights/".format(ds_url)
        response = site.session.get(weights_url)
        weights_info = response.payload
        variables['weights'] = weights_info['graph']
        # Get settings
        if self.verbose:
            print(".", end='')
        settings_url = "{}/settings/".format(ds_url)
        response = site.session.get(settings_url)
        settings_info = response.payload
        self._meta['settings'] = settings_info['body']
        # Get "table" of column definitions
        if self.verbose:
            print(".", end='')
        table_url = "{}/table/".format(ds_url)
        response = site.session.get(table_url)
        table_info = response.payload
        self._meta['table'] = table_info['metadata']
        # That's all
        if self.verbose:
            print("Done.")

    def save(self, filename):
        """Save downloaded metadata to JSON file"""
        if self.verbose:
            print("Saving metadata to:", filename)
        with open(filename, 'wb') as f:
            json.dump(self._meta, f, indent=2, sort_keys=True)
            f.write('\n')

    def load(self, filename):
        """Load downloaded metadata from JSON file"""
        if self.verbose:
            print("Loading metadata from:", filename)
        with open(filename, 'rb') as f:
            self._meta = json.load(f)

    def report(self):
        # general info
        meta = self._meta
        print("Dataset ID:", meta['id'])
        print("name:", meta['name'])
        print("description:", meta['description'])
        print("size:")
        print("  columns:", meta['size']['columns'])
        print("  rows:", meta['size']['rows'])
        print("  unfiltered_rows:", meta['size']['rows'])
        # variable info
        table = meta['table']
        var_type_count_map = defaultdict(int)
        num_vars_with_categories = 0
        unique_cats_lists_without_ids = set()
        unique_cats_lists_with_ids = set()
        tot_categories = 0
        min_categories = None
        max_categories = None
        for var_id, var_def in six.iteritems(table):
            var_type = var_def['type']
            var_type_count_map[var_type] += 1
            if 'categories' in var_def:
                num_vars_with_categories += 1
                categories_list = var_def['categories']
                unique_cats_lists_without_ids.add(
                    make_cats_key(categories_list, remove_ids=True))
                unique_cats_lists_with_ids.add(
                    make_cats_key(categories_list, remove_ids=False))
                num_categories = len(categories_list)
                tot_categories += num_categories
                if min_categories is None or num_categories < min_categories:
                    min_categories = num_categories
                if max_categories is None or num_categories > max_categories:
                    max_categories = num_categories
        print("variables:")
        print("  num. variables:", len(table))
        print("  variables by type:")
        for var_type in sorted(var_type_count_map):
            print("    {}: {}".format(var_type, var_type_count_map[var_type]))
        print("  num. variables with categories:", num_vars_with_categories)
        print("  total categories:", tot_categories)
        print("  min. categories per variable:", min_categories)
        if num_vars_with_categories > 0:
            print("  ave. categories per variable:", float(tot_categories) /
                  num_vars_with_categories)
        print("  max. categories per variable:", max_categories)
        print("  num. unique category lists:")
        print("    with ids:", len(unique_cats_lists_with_ids))
        print("    without ids:", len(unique_cats_lists_without_ids))


def do_get(args):
    ds_id = args['<ds-id>']
    filename = args['<filename>']
    with open(args['-c']) as f:
        config = yaml.safe_load(f)[args['-p']]
    site = connect_pycrunch(config['connection'], verbose=args['-v'])
    meta = MetadataModel(verbose=args['-v'])
    meta.get(site, ds_id)
    meta.save(filename)
    if args['-i']:
        import IPython
        IPython.embed()


def do_info(args):
    filename = args['<filename>']
    meta = MetadataModel(verbose=args['-v'])
    meta.load(filename)
    meta.report()


def main():
    args = docopt.docopt(__doc__)
    t0 = time.time()
    try:
        if args['get']:
            return do_get(args)
        elif args['info']:
            return do_info(args)
        else:
            raise NotImplementedError(
                "Sorry, that command is not yet implemented.")
    finally:
        print("Elapsed time:", time.time() - t0, "seconds", file=sys.stderr)
