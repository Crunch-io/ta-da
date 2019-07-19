#!/usr/bin/env python3
"""
Send requests designed to keep all workers of a zz9 factory busy

Usage:
    dogpile.py [options] <dataset-id>

Options:
    -c CONFIG_FILE          [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: alpha]
    -u USER_ALIAS           Key to section inside profile [default: sim-user-1]
    -v                      Print verbose messages
    --loop-sleep=SECONDS    [default: 1.0]
    --num-runners=N         [default: 15]
"""
from __future__ import print_function
import io
import json
import random
import sys
import threading
import time
import traceback

import docopt
import six
import yaml

import crunch_util
import sim_util


def main():
    args = docopt.docopt(__doc__)
    with io.open(args["-c"], "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)
    dataset_id = args["<dataset-id>"]
    loop_sleep = float(args["--loop-sleep"])
    num_runners = int(args["--num-runners"])
    controller = DogpileController(config, args, dataset_id, loop_sleep)
    runners = []
    try:
        for i in range(1, num_runners + 1):
            name = "Runner-{:02}".format(i)
            runners.append(controller.create_runner(name))
        for runner in runners:
            runner.start()
        while runners:
            runners_copy = runners[:]
            runners = []
            for runner in runners_copy:
                if runner.is_alive():
                    runners.append(runner)
                else:
                    print("{}: died".format(runner.name))
            time.sleep(loop_sleep)
    except KeyboardInterrupt:
        print("\nStarting normal shutdown")
        return 0
    except BaseException:
        traceback.print_exc()
        return 1
    finally:
        print("Signaling runners to stop")
        controller.stop()
        while runners:
            print("Waiting for {} runners to exit...".format(len(runners)))
            for runner in runners:
                runner.join(loop_sleep)
            runners = [r for r in runners if r.is_alive()]
        print("Done.")


class DogpileController:
    def __init__(self, config, args, dataset_id, loop_sleep):
        self.config = config
        self.args = args
        self.dataset_id = dataset_id
        self.loop_sleep = loop_sleep
        self.stop_event = threading.Event()

    def create_runner(self, name):
        return DogpileRunner(self, name)

    def connect_api(self):
        """
        Create a new API session
        Return (site, ds)
        """
        site = sim_util.connect_api(self.config, self.args)
        ds = crunch_util.get_dataset_by_id(site, self.dataset_id)
        return (site, ds)

    def stop(self):
        self.stop_event.set()


class DogpileRunner:
    """
    Look through dataset metadata and arbitrarily pick a variable.
    Do a bunch of read requests on that variable.
    Repeat until stop event is signaled.
    """

    def __init__(self, controller, name):
        self.controller = controller
        self.name = name
        self._thread = None

    def start(self):
        self._thread = threading.Thread(name=self.name, target=self.run)
        self._thread.daemon = True
        self._thread.start()

    def is_alive(self):
        if self._thread is None:
            return False
        return self._thread.is_alive()

    def join(self, timeout=None):
        self._thread.join(timeout)

    def run(self):
        site, ds = self.controller.connect_api()
        metadata = ds.table["metadata"]
        if not metadata:
            raise AssertionError("Dataset must have variables!")
        cat_vars = _get_cat_vars(metadata)
        if not metadata:
            raise AssertionError("Dataset must have at least one categorical variable")
        cat_var_ids = list(cat_vars)
        # Generate random cube requests using single categorical variables
        while not self.controller.stop_event.is_set():
            var_id = random.choice(cat_var_ids)
            # print(var_id)
            # print(json.dumps(var_info, indent=4))
            # @jj would hate this code, oh well
            var_url = ds.variables.by("id")[var_id].entity_url
            params = {
                "dimensions": [{"variable": var_url}],
                "measures": {"count": {"function": "cube_count", "args": []}},
                "weight": None,
            }
            params_str = json.dumps(params, indent=None, separators=(",", ":"))
            print("{}: Cube {}".format(self.name, var_url))
            r = site.session.get(
                ds.views.cube, params={"query": params_str, "filter": "[]"}
            )
            r.raise_for_status()
            time.sleep(self.controller.loop_sleep)


def _get_cat_vars(metadata):
    result = {}
    for var_id, var_info in six.iteritems(metadata):
        if var_info["type"] == "categorical":
            result[var_id] = var_info
    return result


if __name__ == "__main__":
    sys.exit(main())
