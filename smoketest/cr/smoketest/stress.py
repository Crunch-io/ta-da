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


def run_stress_loop(
    config,
    num_agents=1,
    verbose=False,
    idle_timeout=120,
    cleaner_delay=180,
    sparse_data=False,
    num_rows=1000,
    do_cleanup=True,
):
    print("Running", num_agents, "stress agents(s), press Ctr-C to stop.")
    stop_event = threading.Event()
    kwargs = dict(
        idle_timeout=idle_timeout,
        cleaner_delay=cleaner_delay,
        verbose=verbose,
        sparse_data=sparse_data,
        num_rows=num_rows,
        do_cleanup=do_cleanup,
    )
    agents = []
    try:
        for agent_id in range(num_agents):
            agent = StressAgent(agent_id, config, stop_event, **kwargs)
            agent.start()
            agents.append(agent)
            # Delay to avoid hitting race condition creating datasets
            # Filed ticket: https://www.pivotaltracker.com/story/show/162001536
            time.sleep(1.0)
        while True:
            # Wait for Ctrl-C
            time.sleep(idle_timeout)
    except KeyboardInterrupt:
        print("\nCtrl-C received, quitting main stress loop...")
        stop_event.set()
        for agent in agents:
            agent.join()
    finally:
        print("Finished main stress loop.")


class StressAgent:
    def __init__(
        self,
        agent_id,
        config,
        stop_event,
        idle_timeout=120,
        cleaner_delay=180,
        verbose=False,
        sparse_data=False,
        num_rows=1000,
        do_cleanup=True,
    ):
        self.agent_id = agent_id
        self.config = config
        self.stop_event = stop_event
        self.idle_timeout = idle_timeout
        self.cleaner_delay = cleaner_delay
        self.verbose = verbose
        self.sparse_data = sparse_data
        self.num_rows = num_rows
        self.do_cleanup = do_cleanup
        #####
        self.writer_thread = None
        self.reader_thread = None

    def start(self):
        self.writer_thread = t = threading.Thread(target=self._run_writer)
        t.daemon = True
        t.start()

    def join(self):
        if self.writer_thread is not None:
            self.writer_thread.join()
            self.writer_thread = None
        if self.reader_thread is not None:
            self.reader_thread.join()
            self.reader_thread = None

    def _run_writer(self):
        print("Agent {}:".format(self.agent_id), "Beginning main thread")
        site = connect_pycrunch(self.config["connection"], verbose=self.verbose)
        metadata_path = os.path.join(this_dir, "data", "dataset.json")
        with open(metadata_path) as f:
            metadata = json.load(f)
        f = None  # create dataset with no rows
        t = datetime.datetime.now()
        dataset_name = "Stress Test {}".format(t.isoformat(" "))
        ds = create_dataset_from_csv(
            site, metadata, f, verbose=self.verbose, dataset_name=dataset_name
        )
        print("Agent {}:".format(self.agent_id), "Created dataset:", ds.self)
        event = self.stop_event
        try:
            max_cols = 100
            var_aliases = collections.deque()
            while not event.is_set() and len(var_aliases) < max_cols:
                var_alias, n = _append_random_numeric_column(ds)
                print(
                    "Agent {}:".format(self.agent_id),
                    "Added column",
                    var_alias,
                    "with",
                    n,
                    "rows.",
                )
                var_aliases.append(var_alias)
            num_appends_between_cleans = 10
            num_appends_since_clean = 0
            while not event.is_set():
                print(
                    "Agent {}:".format(self.agent_id),
                    "Appending",
                    self.num_rows,
                    "rows to dataset",
                    ds.self,
                )
                _append_random_rows(
                    site, ds, self.num_rows, sparse_data=self.sparse_data
                )
                num_appends_since_clean += 1
                if num_appends_since_clean >= num_appends_between_cleans:
                    # Pause to let cleaner run
                    clean_wait = self.idle_timeout + self.cleaner_delay
                    print(
                        "Agent {}:".format(self.agent_id),
                        "Waiting",
                        clean_wait,
                        "seconds for cleaner run.",
                    )
                    event.wait(clean_wait)
                    num_appends_since_clean = 0
        finally:
            print(
                "Agent {}:".format(self.agent_id),
                "Leaving loop that was stressing dataset:",
                ds.self,
            )
            if self.do_cleanup:
                print("Agent {}:".format(self.agent_id), "Deleting dataset:", ds.self)
                site.session.delete(ds.self)


def _append_random_rows(site, ds, num_rows, sparse_data=False):
    metadata = get_ds_metadata(ds)
    var_defs = metadata["body"]["table"]["metadata"]
    pk = get_pk_alias(ds)
    with open_csv_tempfile() as f:
        write_random_rows(var_defs, pk, num_rows, f, sparse_data=sparse_data)
        f.seek(0)
        append_csv_file_to_dataset(site, ds, f, verbose=False)


def _make_varname(prefix="v_"):
    t = datetime.datetime.now()
    characters = string.ascii_lowercase + string.digits
    choice = random.choice
    suffix = "".join(choice(characters) for _ in range(5))
    return "".join([prefix, t.strftime("%Y%m%d%H%M%S_%f"), "_", suffix])


def _append_random_numeric_column(ds):
    var_name = _make_varname()
    info = ds.summary
    # weighted and unweighted rows seem to overlap
    num_rows = max(info.value.weighted.total, info.value.unweighted.total)
    values = [random.random() * 100.0 for _ in six.moves.range(num_rows)]
    r = ds.variables.post(
        {"name": var_name, "alias": var_name, "type": "numeric", "values": values}
    )
    r.raise_for_status()
    return var_name, num_rows
