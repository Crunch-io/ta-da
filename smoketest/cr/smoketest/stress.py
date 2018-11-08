"""
Stress Crunch by creating, updating, and deleting datasets continously
"""
from __future__ import print_function
import datetime
import json
import os
import random
import string
import sys
import time

import six

from .crunch_util import (
    append_csv_file_to_dataset,
    connect_pycrunch,
    create_dataset_from_csv,
    get_ds_metadata,
    get_pk_alias,
)
from .gen_data import open_csv_tempfile, write_random_rows

this_module = sys.modules[__name__]
this_dir = os.path.dirname(os.path.abspath(this_module.__file__))


def run_stress_loop(config, num_threads=1, verbose=False):
    # TODO: Actually use num_threads
    print("Running stress loop, press Ctr-C to stop.")
    site = connect_pycrunch(config['connection'], verbose=verbose)
    metadata_path = os.path.join(this_dir, 'data', 'dataset.json')
    with open(metadata_path) as f:
        metadata = json.load(f)
    f = None  # create dataset with no rows
    t = datetime.datetime.now()
    dataset_name = "Stress Test {}".format(t.isoformat(' '))
    ds = create_dataset_from_csv(site, metadata, f, verbose=False,
                                 dataset_name=dataset_name)
    print("Created dataset:", ds.self)
    try:
        _run_stress_loop(site, ds)
    finally:
        print("Deleting dataset:", ds.self)
        site.session.delete(ds.self)


def _run_stress_loop(site, ds):
    num_rows = 10000
    print("Appending", num_rows, "rows to dataset", ds.self)
    _append_random_rows(site, ds, num_rows)
    cycle_delay = 10.0  # seconds
    try:
        while True:
            var_alias, n = _append_random_numeric_column(ds)
            print("Added column", var_alias, "with", n, "rows.")
            time.sleep(cycle_delay)
    except KeyboardInterrupt:
        print("\nCtrl-C received, quitting...")


def _append_random_rows(site, ds, num_rows):
    metadata = get_ds_metadata(ds)
    var_defs = metadata['body']['table']['metadata']
    pk = get_pk_alias(ds)
    with open_csv_tempfile() as f:
        write_random_rows(var_defs, pk, num_rows, f)
        f.seek(0)
        append_csv_file_to_dataset(site, ds, f, verbose=False)


def _make_varname(prefix='v_'):
    t = datetime.datetime.now()
    characters = string.ascii_lowercase + string.digits
    choice = random.choice
    suffix = ''.join(choice(characters) for _ in range(5))
    return ''.join([prefix, t.strftime('%Y%m%d%H%M%S_%f'), '_', suffix])


def _append_random_numeric_column(ds):
    var_name = _make_varname()
    info = ds.summary
    # weighted and unweighted rows seem to overlap
    num_rows = max(info.value.weighted.total, info.value.unweighted.total)
    values = [random.random() * 100.0 for _ in six.moves.range(num_rows)]
    r = ds.variables.post({
        'name': var_name,
        'alias': var_name,
        'type': 'numeric',
        'values': values,
    })
    r.raise_for_status()
    return var_name, num_rows
