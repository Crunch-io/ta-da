"""
Stress Crunch by creating, updating, and deleting datasets continously
"""
from __future__ import print_function
import collections
import datetime
import json
import os
import random
import string
import sys
import threading
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


def run_stress_loop(config, num_threads=1, verbose=False, idle_timeout=120,
                    sparse_data=False, num_rows=1000):
    print("Running", num_threads, "stress loop thread(s), press Ctr-C to stop.")
    threads = []
    event = threading.Event()
    kwargs = dict(idle_timeout=idle_timeout, verbose=verbose,
                  sparse_data=sparse_data,
                  num_rows=num_rows)
    try:
        for loop_id in range(num_threads):
            args = (config, loop_id, event)
            t = threading.Thread(target=_run_stress_loop, args=args,
                                 kwargs=kwargs)
            t.daemon = True
            t.start()
            threads.append(t)
            # Delay to avoid hitting race condition creating datasets
            # Filed ticket: https://www.pivotaltracker.com/story/show/162001536
            time.sleep(1.0)
        while True:
            # Wait for Ctrl-C
            time.sleep(idle_timeout)
    except KeyboardInterrupt:
        print("\nCtrl-C received, quitting main stress loop...")
        event.set()
        for t in threads:
            t.join()
    finally:
        print("Finished main stress loop.")


def _run_stress_loop(config, loop_id, event,
                     idle_timeout=120, cleaner_delay=30, verbose=False,
                     sparse_data=False,
                     num_rows=1000):
    print("{}:".format(loop_id), "Beginning stress loop")
    site = connect_pycrunch(config['connection'], verbose=verbose)
    metadata_path = os.path.join(this_dir, 'data', 'dataset.json')
    with open(metadata_path) as f:
        metadata = json.load(f)
    f = None  # create dataset with no rows
    t = datetime.datetime.now()
    dataset_name = "Stress Test {}".format(t.isoformat(' '))
    ds = create_dataset_from_csv(site, metadata, f, verbose=verbose,
                                 dataset_name=dataset_name)
    print("{}:".format(loop_id), "Created dataset:", ds.self)
    try:
        max_cols = 100
        print("{}:".format(loop_id),
              "Appending", num_rows, "rows to dataset", ds.self)
        _append_random_rows(site, ds, num_rows,
                            sparse_data=sparse_data)
        var_aliases = collections.deque()
        num_deletes_since_clean = 0
        while not event.is_set():
            var_alias, n = _append_random_numeric_column(ds)
            print("{}:".format(loop_id),
                  "Added column", var_alias, "with", n, "rows.")
            var_aliases.append(var_alias)
            if len(var_aliases) > max_cols:
                # We have all the columns we need, remove one
                var_alias = var_aliases.popleft()
                v = ds.variables.by('alias')[var_alias]
                print("{}:".format(loop_id),
                      "Deleting variable", var_alias)
                r = v.entity.delete()
                r.raise_for_status()
                num_deletes_since_clean += 1
            if num_deletes_since_clean >= max_cols:
                # We've deleted a bunch of columns, now let cleaner run
                num_deletes_since_clean = 0
                clean_wait = idle_timeout + cleaner_delay + 150
                print("{}:".format(loop_id),
                      "Waiting", clean_wait, "seconds for cleaner run.")
                event.wait(clean_wait)
    finally:
        print("{}:".format(loop_id),
              "Leaving stress loop, deleting dataset:", ds.self)
        site.session.delete(ds.self)


def _append_random_rows(site, ds, num_rows, sparse_data=False):
    metadata = get_ds_metadata(ds)
    var_defs = metadata['body']['table']['metadata']
    pk = get_pk_alias(ds)
    with open_csv_tempfile() as f:
        write_random_rows(var_defs, pk, num_rows, f,
                          sparse_data=sparse_data)
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
