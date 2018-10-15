"""
Crunch Smoke Test Suite

Usage:
    cr.smoketest [options] pick-random-dataset [--zz9repo=REPODIR]
    cr.smoketest [options] append-random-rows [--num-rows=NUMROWS] <dataset-id>
    cr.smoketest [options] get-metadata <dataset-id> [<output-filename>]

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -v                      Print verbose messages
    -i                      Start ipython after some commands
    --num-rows=NUMROWS      [default: 10]
    --zz9repo=REPODIR       [default: /var/lib/crunch.io/zz9repo]

Commands:
    pick-random-dataset
        Look at the zz9repo dir, print random datasetID
    append-random-rows
        Read a dataset variable definitions, generate compatible CSV rows,
        append those rows to the dataset.
    get-metadata
        Query dataset metadata and save it in JSON format
"""
from __future__ import print_function
from collections import OrderedDict
import json
import os
import random
import sys

import docopt
import six
from six.moves.urllib import parse as urllib_parse
import yaml

from .crunch_util import append_csv_file_to_dataset, connect_pycrunch
from .gen_data import open_csv_tempfile, write_random_rows

this_module = sys.modules[__name__]


###########################
# Helper functions


def load_config(args):
    with open(args['-c']) as f:
        config = yaml.safe_load(f)[args['-p']]
    return config


def pick_random_dataset(zz9repo='/var/lib/crunch.io/zz9repo'):
    prefix_dirs = os.listdir(zz9repo)
    while prefix_dirs:
        prefix = random.choice(prefix_dirs)
        prefix_dirs.remove(prefix)
        dataset_dirs = os.listdir(os.path.join(zz9repo, prefix))
        if dataset_dirs:
            return random.choice(dataset_dirs)
    raise Exception("No datasets to choose from.")


def get_ds_metadata(ds, set_derived_field=True):
    """
    ds: pycrunch dataset returned by site.datasets.by('id')[ds_id].entity
    Return a dictionary containing metadata for this dataset, see:
        http://docs.crunch.io/feature-guide/feature-importing.html#example
    """
    response = ds.session.get(ds.table.self)
    response.raise_for_status()
    table = response.json()
    if 'description' in table:
        del table['description']
    if 'self' in table:
        del table['self']
    result = OrderedDict()
    result["element"] = "shoji:entity"
    result["body"] = body = OrderedDict()
    body["name"] = ds.body['name']
    body["description"] = ds.body['description']
    body["table"] = table
    if set_derived_field:
        for var_url, var_info in six.iteritems(ds.variables.index):
            if var_info['derived']:
                var_id = urllib_parse.urlparse(var_url).path.rsplit('/', 2)[-2]
                table['metadata'][var_id]['derived'] = True
    return result


def get_pk_alias(ds):
    """
    ds: pycrunch dataset returned by site.datasets.by('id')[ds_id].entity
    Return the alias of the PK column, or None if no Primary Key.
    Raise an exception if there are multiple PKs (is that allowed?)
    """
    pk_info = ds.pk
    pk_url_list = pk_info.body.pk
    if not pk_url_list:
        return None
    if len(pk_url_list) > 1:
        raise RuntimeError("Can't handle {} PKs in dataset {}"
                           .format(len(pk_url_list), ds.id))
    pk_url = pk_url_list[0]
    response = ds.session.get(pk_url)
    response.raise_for_status()
    pk_alias = response.json()['body']['alias']
    return pk_alias


###########################
# Command functions

def do_pick_random_dataset(args):
    zz9repo = args['--zz9repo']
    print(pick_random_dataset(zz9repo))


def do_get_metadata(args):
    config = load_config(args)
    site = connect_pycrunch(config['connection'], verbose=args['-v'])
    ds_id = args['<dataset-id>']
    ds = site.datasets.by('id')[ds_id].entity
    metadata = get_ds_metadata(ds)
    if not args['<output-filename>']:
        out = sys.stdout
    else:
        out = open(args['<output-filename>'], 'w')
    try:
        json.dump(metadata, out, indent=4, sort_keys=True)
        out.write('\n')
    finally:
        if args['<output-filename>']:
            out.close()
    if args['-i']:
        import IPython
        IPython.embed()


def do_append_random_rows(args):
    config = load_config(args)
    site = connect_pycrunch(config['connection'], verbose=args['-v'])
    ds_id = args['<dataset-id>']
    ds = site.datasets.by('id')[ds_id].entity
    metadata = get_ds_metadata(ds)
    var_defs = metadata['body']['table']['metadata']
    pk = get_pk_alias(ds)
    num_rows = int(args['--num-rows'])
    with open_csv_tempfile() as f:
        write_random_rows(var_defs, pk, num_rows, f)
        f.seek(0)
        append_csv_file_to_dataset(site, ds, f, verbose=args['-v'])


def main():
    args = docopt.docopt(__doc__)
    for key, value in six.iteritems(args):
        if not key[:1] in ('-', '<') and value:
            command_name = key.lower().replace('-', '_')
            command_func = getattr(this_module, 'do_' + command_name, None)
            if command_func:
                return command_func(args)
            raise ValueError("Invalid subcommand: {}".format(command_name))
    raise ValueError("Invalid or missing subcommand.")


if __name__ == '__main__':
    main()
