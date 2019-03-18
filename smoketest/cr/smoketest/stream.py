"""
Stress Crunch by streaming messages to a dataset continously
"""
from __future__ import print_function
import collections
import datetime
import json
import os
import random
import sys
import threading
import time

import six

from .crunch_util import connect_pycrunch, create_dataset_from_csv, set_pk_alias

this_module = sys.modules[__name__]
this_dir = os.path.dirname(os.path.abspath(this_module.__file__))


def run_stream_loop(config, num_agents=1, verbose=False, do_cleanup=True):
    print("Running", num_agents, "stress agents(s), press Ctr-C to stop.")
    stop_event = threading.Event()
    kwargs = dict(verbose=verbose, do_cleanup=do_cleanup)
    agents = []
    try:
        for agent_id in range(num_agents):
            agent = StreamAgent(agent_id, config, stop_event, **kwargs)
            agent.start()
            agents.append(agent)
            # Delay to avoid hitting race condition creating datasets
            # Filed ticket: https://www.pivotaltracker.com/story/show/162001536
            time.sleep(1.0)
        while True:
            # Wait for Ctrl-C
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nCtrl-C received, quitting main stress loop...")
        stop_event.set()
        for agent in agents:
            agent.join()
    finally:
        print("Finished main stress loop.")


class StreamAgent:
    def __init__(self, agent_id, config, stop_event, verbose=False, do_cleanup=True):
        self.agent_id = agent_id
        self.config = config
        self.stop_event = stop_event
        self.verbose = verbose
        self.do_cleanup = do_cleanup
        #####
        self.writer_thread = None
        self.reader_thread = None

    def start(self):
        self.writer_thread = threading.Thread(target=self._run_writer)
        self.writer_thread.daemon = True
        self.writer_thread.start()

    def join(self):
        if self.writer_thread is not None:
            self.writer_thread.join()
            self.writer_thread = None
        if self.reader_thread is not None:
            self.reader_thread.join()
            self.reader_thread = None

    def _create_dataset(self, site):
        metadata_path = os.path.join(this_dir, "data", "dataset-with-pk.json")
        with open(metadata_path) as f:
            metadata = json.load(f)
        f = None  # create dataset with no rows
        t = datetime.datetime.now()
        dataset_name = "Stream Test {}".format(t.isoformat(" "))
        ds = create_dataset_from_csv(
            site, metadata, f, verbose=self.verbose, dataset_name=dataset_name
        )
        ds_id = ds.body["id"]
        print("Agent {}:".format(self.agent_id), "Writer created dataset:", ds_id)
        pk_alias = "personid"
        set_pk_alias(ds, pk_alias)
        print("Agent {}:".format(self.agent_id), "Writer set PK alias:", pk_alias)
        return ds

    def _run_writer(self):
        print("Agent {}:".format(self.agent_id), "Writer thread started")
        site = connect_pycrunch(self.config["connection"], verbose=self.verbose)
        ds = self._create_dataset(site)
        self.reader_thread = threading.Thread(
            target=self._run_reader, args=(ds.body["id"],)
        )
        self.reader_thread.daemon = True
        self.reader_thread.start()
        try:
            max_cols = 100
            var_aliases = collections.deque()
            while not self.stop_event.is_set() and len(var_aliases) < max_cols:
                var_alias, n = _append_random_numeric_column(ds)
                print(
                    "Agent {}:".format(self.agent_id),
                    "Writer added column",
                    var_alias,
                    "with",
                    n,
                    "rows.",
                )
                var_aliases.append(var_alias)
            num_appends_between_cleans = 10
            num_appends_since_clean = 0
            while not self.stop_event.is_set():
                print(
                    "Agent {}:".format(self.agent_id),
                    "Writer appending",
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
                        "Writer waiting",
                        clean_wait,
                        "seconds for cleaner run.",
                    )
                    self.stop_event.wait(clean_wait)
                    num_appends_since_clean = 0
        finally:
            print(
                "Agent {}:".format(self.agent_id),
                "Writer leaving loop that was stressing dataset:",
                ds.self,
            )
            if self.do_cleanup:
                print(
                    "Agent {}:".format(self.agent_id),
                    "Writer deleting dataset:",
                    ds.self,
                )
                site.session.delete(ds.self)

    def _run_reader(self, ds_id):
        print("Agent {}:".format(self.agent_id), "Reader thread started")
        site = connect_pycrunch(self.config["connection"], verbose=self.verbose)
        ds = site.datasets.by("id")[ds_id].entity
        while not self.stop_event.is_set():
            print(
                "Agent {}:".format(self.agent_id),
                "Reader fetching metadata from dataset",
                ds.self,
            )
            get_ds_metadata(ds)
            delay = random.random() * 10
            print("Agent {}:".format(self.agent_id), "Reader waiting", delay, "seconds")
            self.stop_event.wait(delay)


def _append_random_rows(site, ds, num_rows, sparse_data=False):
    metadata = get_ds_metadata(ds)
    var_defs = metadata["body"]["table"]["metadata"]
    pk = get_pk_alias(ds)
    with open_csv_tempfile() as f:
        write_random_rows(var_defs, pk, num_rows, f, sparse_data=sparse_data)
        f.seek(0)
        append_csv_file_to_dataset(site, ds, f, verbose=False)


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
