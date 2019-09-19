#!/usr/bin/env python3
"""
Dynamically monitor whichever zz9 process is hosting a particular dataset.

Usage:
    zz9_mon.py [options] monitor
    zz9_mon.py [options] ps [--sort-by=SORT] [-n N]
    zz9_mon.py [options] top [--sort-by=SORT]

Options:
    --zz9-config=FILENAME   [default: /var/lib/crunch.io/zz9-0.conf]
    --interval=SECONDS      [default: 2.0]
    --sort-by=SORT_COL      [default: -active,-rss] Sort columns, comma-separated
    -n N                    [default: auto] Print the first N items, -1 for all
    -v                      Print verbose messages

Commands:
    monitor     Monitor the zz9 factory hosting a particular dataset
    ps          Print a snapshot of statistics of current zz9d processes
    top         Continously refresh screen every interval seconds

Sorting:
    The sort column names are: pid zz9 cpu rss ds active
    The "active" pseudo-column is 1 if there is a dataset, 0 otherwise.
    Put a "-" in front of a sort col to sort in descending order.
    To list the top 10 CPU-consuming zz9d processes:

        ./mon_zz9.py ps --sort-by=-cpu -n 10
"""
from datetime import datetime
import json
import operator
import re
import shutil
import subprocess
import sys
import time
import traceback
from urllib.parse import urlparse

import docopt
import psutil
import redis

ZZ9_PORT_BASE = 22900
G = 1024 * 1024 * 1024


def get_zz9_ip_addr_index(factory_url):
    """
    factory_url: Result from factory_map.get(dataset_id)
    Return (zz9_ip_addr, zz9_index) or (None, None)
    """
    if not factory_url:
        return (None, None)
    p = urlparse(factory_url)
    if p.scheme != b"tcp":
        return (None, None)
    parts = p.netloc.split(b":")
    if len(parts) != 2:
        raise ValueError(f"Invalid factory URL: {factory_url}")
    zz9_ip_addr = parts[0].decode("utf-8")
    zz9_port = int(parts[1])
    if zz9_port < ZZ9_PORT_BASE or zz9_port >= (ZZ9_PORT_BASE + 100):
        raise ValueError(f"Invalid port {zz9_port} in factory URL: {factory_url}")
    zz9_index = zz9_port - ZZ9_PORT_BASE
    return (zz9_ip_addr, zz9_index)


def get_host_ips():
    try:
        r = subprocess.run(
            ["hostname", "-I"], timeout=1.0, input=b"", stdout=subprocess.PIPE
        )
    except Exception:
        return []
    if r.returncode != 0:
        return []
    return [i.decode("utf-8") for i in r.stdout.split()]


def get_zz9_process_map():
    """Return map of zz9_index to psutil.Process object"""
    regex = re.compile(r"\bzz9-(?P<zz9_index>\d+)\b")
    zz9_process_map = {}
    for process in psutil.process_iter(attrs=["pid", "name"]):
        name = process.info["name"]
        m = regex.search(name)
        if not m:
            # Not a zz9d process
            continue
        zz9_index = int(m.group("zz9_index"))
        zz9_process_map[zz9_index] = process
    return zz9_process_map


def get_pid_cpu_percent_map(pid_set):
    # Return {pid: cpu_percent} for all process IDs in pid_set
    result = {}
    for process in psutil.process_iter(attrs=["pid", "cpu_percent"]):
        pid = process.info["pid"]
        if pid not in pid_set:
            continue
        result[pid] = process.info["cpu_percent"]
    return result


def get_dataset_map(factory_map, host_ip_addr):
    """
    factory_map: Redis database mapping dataset_id to factory_url
    host_ip_addr: This host's IP address, used to filter factory URLs
    Return map of dataset_id to zz9_index (last two digits of port number)
    """
    dataset_map = {}
    for dataset_id in factory_map.scan_iter():
        dataset_id = dataset_id.decode("utf-8")
        if dataset_id.startswith("__"):
            continue
        factory_url = factory_map.get(dataset_id)
        zz9_ip_addr, zz9_index = get_zz9_ip_addr_index(factory_url)
        if zz9_ip_addr != host_ip_addr:
            continue
        dataset_map[dataset_id] = zz9_index
    return dataset_map


class DatasetResourceMonitor:
    def __init__(self, command, args, host_ip_addr, factory_map):
        self.command = command
        self.args = args
        self.host_ip_addr = host_ip_addr
        self.factory_map = factory_map

    def run(self):
        # Don't exit with unhandled exception or we'll get Sentry messages
        try:
            self._run()
        except KeyboardInterrupt:
            print("\nStopped.", file=sys.stderr)
            return 0
        except Exception:
            traceback.print_exc()
            return 1

    def _run(self):
        cmd_method = getattr(self, f"_do_{self.command}", None)
        if cmd_method is None:
            raise NotImplementedError(f"Unimplemented command: {self.command}")
        return cmd_method()

    def _do_top(self):
        # Like the ps command but repeated every interval seconds until Ctrl-C
        interval_sec = float(self.args["--interval"])
        while True:
            print("\x1b[2J", end="")  # clear the screen
            print("\x1b[1;1H", end="")  # move cursor to upper left
            ts = datetime.now().isoformat(sep=" ", timespec="milliseconds")
            gmem = psutil.virtual_memory()
            zz9_proc_info_list = self._get_zz9_proc_info_list()
            limit = max(shutil.get_terminal_size().lines - 12, 10)
            self._print_zz9_proc_info_header(ts, gmem, zz9_proc_info_list, limit)
            self._print_zz9_proc_info_body(gmem, zz9_proc_info_list, limit)
            sys.stdout.flush()
            time.sleep(interval_sec)

    def _do_ps(self):
        # We have to gather the info twice, because you need some history in
        # order to get non-zero cpu percent info.  We will use the memory info
        # from pass 1, cpu info from pass 2.
        ts = datetime.now().isoformat(sep=" ", timespec="milliseconds")
        gmem = psutil.virtual_memory()
        zz9_proc_info_list = self._get_zz9_proc_info_list()
        limit = self.args["-n"]
        if limit == "auto":
            limit = max(shutil.get_terminal_size().lines - 12, 10)
        else:
            limit = int(limit)
        interval_sec = float(self.args["--interval"])

        # Print the header before pausing
        self._print_zz9_proc_info_header(ts, gmem, zz9_proc_info_list, limit)
        sys.stdout.flush()

        time.sleep(interval_sec)

        # Gather and merge in updated cpu percent info
        pid_cpu_percent_map = get_pid_cpu_percent_map(
            set(row[0] for row in zz9_proc_info_list)
        )

        def _merge_cpu_percent(row):
            pid, zz9_index, cpu_percent, rss, dataset_id = row
            cpu_percent = pid_cpu_percent_map.get(pid, cpu_percent)
            return (pid, zz9_index, cpu_percent, rss, dataset_id)

        zz9_proc_info_list = [_merge_cpu_percent(row) for row in zz9_proc_info_list]

        self._print_zz9_proc_info_body(gmem, zz9_proc_info_list, limit)
        sys.stdout.flush()

    def _print_zz9_proc_info_header(self, ts, gmem, zz9_proc_info_list, limit):
        print(
            f"{ts}"
            f" total mem: {gmem.total / G:7.3f}G"
            f" avail mem: {gmem.available / G:7.3f}G"
            f" %used: {gmem.percent:5.1f}%"
        )
        print(f"{len(zz9_proc_info_list)} zz9d processes", end="")
        if limit >= 0:
            print(f", showing up to {limit}", end="")
        print(f", sorted by {self.args['--sort-by']}:")
        print("   pid zz9  cpu%  rss(G) ds")
        print("------  -- ----- ------- --------------------------------")

    def _print_zz9_proc_info_body(self, gmem, zz9_proc_info_list, limit):
        total_zz9_rss = 0.0
        active_zz9_rss = 0.0
        active_zz9_count = 0
        idle_zz9_rss = 0.0
        idle_zz9_count = 0
        filtered_zz9_rss = 0.0
        filtered_zz9_count = 0
        for (i, (pid, zz9_index, cpu_percent, rss, dataset_id)) in enumerate(
            zz9_proc_info_list
        ):
            total_zz9_rss += rss
            if dataset_id:
                active_zz9_rss += rss
                active_zz9_count += 1
            else:
                idle_zz9_rss += rss
                idle_zz9_count += 1
            if limit < 0 or i < limit:
                filtered_zz9_rss += rss
                filtered_zz9_count += 1
                cpu = f"{cpu_percent:5.1f}"
                rss = f"{rss / G:7.3f}"
                ds = "" if dataset_id is None else dataset_id
                print(f"{pid:6d}  {zz9_index:02d} {cpu} {rss} {ds}")
        if limit > 0:
            print("                 -------")
            filtered_zz9_percent = (filtered_zz9_rss / gmem.total) * 100.0
            print(
                f"Filtered ({filtered_zz9_count:2d}):   {filtered_zz9_rss / G:7.3f}"
                f" ({filtered_zz9_percent:5.1f}% of total mem)"
            )
        total_zz9_percent = (total_zz9_rss / gmem.total) * 100.0
        active_zz9_percent = (active_zz9_rss / gmem.total) * 100.0
        idle_zz9_percent = (idle_zz9_rss / gmem.total) * 100.0
        other_rss = (gmem.total - gmem.available) - total_zz9_rss
        other_rss_percent = (other_rss / gmem.total) * 100.0
        print("                 -------")
        print(
            f"Active   ({active_zz9_count:2d}):   {active_zz9_rss / G:7.3f}"
            f" ({active_zz9_percent:5.1f}% of total mem)"
        )
        print(
            f"Idle     ({idle_zz9_count:2d}):   {idle_zz9_rss / G:7.3f}"
            f" ({idle_zz9_percent:5.1f}% of total mem)"
        )
        print(
            f"All zz9  ({len(zz9_proc_info_list):2d}):   {total_zz9_rss / G:7.3f}"
            f" ({total_zz9_percent:5.1f}% of total mem)"
        )
        print(
            f"Non-zz9d mem :   {other_rss / G:7.3f}"
            f" ({other_rss_percent:5.1f}% of total mem)"
        )

    def _get_zz9_proc_info_list(self):
        """
        Return list of tuples in this format:
            (pid, zz9_index, cpu_percent, rss, dataset_id)
        sorted according to the "--sort-by" option.
        """
        dataset_map = get_dataset_map(self.factory_map, self.host_ip_addr)
        zz9_index_map = dict(map(reversed, dataset_map.items()))
        zz9_process_map = get_zz9_process_map()
        result = []
        for zz9_index, process in zz9_process_map.items():
            dataset_id = zz9_index_map.get(zz9_index, "")
            try:
                with process.oneshot():
                    pid = process.pid
                    cpu_percent = process.cpu_percent()
                    rss = process.memory_info().rss
            except psutil.NoSuchProcess:
                pid = -1
                cpu_percent = 0.0
                rss = 0.0
            result.append((pid, zz9_index, cpu_percent, rss, dataset_id))

        return self._sort_zz9_proc_info_list(result)

    def _sort_zz9_proc_info_list(self, proc_info_list):
        result = proc_info_list[:]
        sort_cols = self.args["--sort-by"]
        if not sort_cols:
            return result

        sort_cols = [i.strip() for i in sort_cols.split(",") if i.strip()]
        data_cols = ("pid", "zz9", "cpu", "rss", "ds")

        def _active(row):
            # 1 if there is a dataset ID else 0
            return 1 if row[4] else 0

        for sort_col in reversed(sort_cols):
            reverse = sort_col.startswith("-")
            sort_col = sort_col.lstrip("-")
            if sort_col == "active":
                key_func = _active
            else:
                try:
                    sort_col_index = data_cols.index(sort_col)
                except ValueError:
                    raise ValueError(f"Invalid sort column name: {sort_col}")
                else:
                    key_func = operator.itemgetter(sort_col_index)
            result.sort(key=key_func, reverse=reverse)

        return result

    def _do_monitor(self):
        interval_sec = float(self.args["--interval"])
        while True:
            ts = datetime.now().isoformat(sep=" ", timespec="milliseconds")
            gmem = psutil.virtual_memory()
            zz9_proc_info_list = self._get_zz9_proc_info_list()
            idle_zz9_count = 0
            idle_zz9_cpu = 0.0
            idle_zz9_rss = 0.0
            for (_pid, zz9_index, cpu_percent, rss, dataset_id) in zz9_proc_info_list:
                if not dataset_id:
                    idle_zz9_count += 1
                    idle_zz9_cpu = max(idle_zz9_cpu, cpu_percent)
                    idle_zz9_rss += rss
                    continue
                msg = {
                    "ts": ts,
                    "ds": dataset_id,
                    "zz9": zz9_index,
                    "count": 1,
                    "total_mem": gmem.total / G,
                    "avail_mem": gmem.available / G,
                    "mem_percent_used": gmem.percent,
                    "cpu": cpu_percent,
                    "rss": rss / G,
                }
                json.dump(msg, sys.stdout)
                sys.stdout.write("\n")
                sys.stdout.flush()

            msg = {
                "ts": ts,
                "ds": None,
                "zz9": None,
                "count": idle_zz9_count,
                "total_mem": gmem.total / G,
                "avail_mem": gmem.available / G,
                "mem_percent_used": gmem.percent,
                "cpu": idle_zz9_cpu,
                "rss": idle_zz9_rss / G,
            }
            json.dump(msg, sys.stdout)
            sys.stdout.write("\n")
            sys.stdout.flush()

            time.sleep(interval_sec)


def main():
    args = docopt.docopt(__doc__)
    command = None
    for arg, value in args.items():
        if not value or arg.startswith(("-", "<")):
            continue
        command = arg
        break
    else:
        raise ValueError("Missing command")
    zz9_config_file = args["--zz9-config"]
    if args["-v"]:
        print(f"Loading config from {zz9_config_file}")
    with open(zz9_config_file, "r") as f:
        zz9_config = json.load(f)
    if len(zz9_config) != 1:
        raise RuntimeError("More than one zone per config not supported")
    zone_name = list(zz9_config)[0]
    factory_map_url = zz9_config[zone_name]["factories"]["map"]
    if args["-v"]:
        print(f"Connecting to redis at {factory_map_url}")
    factory_map = redis.Redis.from_url(factory_map_url)
    host_ips = get_host_ips()
    if len(host_ips) < 1:
        raise RuntimeError("Couldn't get host IP address")
    if len(host_ips) > 1:
        print(
            "WARNING: {} host IP addrs found, picking the first one".format(
                len(host_ips)
            )
        )
    host_ip_addr = host_ips[0]
    mon = DatasetResourceMonitor(
        command=command, args=args, host_ip_addr=host_ip_addr, factory_map=factory_map
    )
    return mon.run()


if __name__ == "__main__":
    sys.exit(main())
