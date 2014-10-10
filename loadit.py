#!/usr/bin/env python
"""A helper to load your system."""
import multiprocessing
cpu_count = multiprocessing.cpu_count()
import subprocess
import sys

from docopt import docopt

proc_meminfo = {}
with open("/proc/meminfo", "rb") as lines:
    for line in lines:
        k, v = line.split(":", 1)

        atoms = v.strip().split(" ", 1)
        if len(atoms) == 1:
            amt = int(atoms[0])
        elif len(atoms) == 2:
            amt = int(atoms[0].strip())
            scale = atoms[1].strip().lower()
            if scale == 'kb':
                amt *= 1000
            elif scale == 'mb':
                amt *= 1000000
            else:
                print "Unparsable scale in /proc/meminfo:", line
        else:
            print "Unparsable entry in /proc/meminfo:", line

        proc_meminfo[k] = amt


def main():
    """The entry point for loadit."""
    helpstr = """Load CPUs and memory.

Usage:
  loadit.py [options]
  loadit.py (-h | --help)

Options:
  -h, --help            Show this screen.
  -p, --processes <int> The number of processes to load [default: %(cpu_count)s].
  -m, --memory <float>  The percent of total memory (%(memtotal)d) to reserve [default: 100].
""" % {"cpu_count": cpu_count, "memtotal": proc_meminfo['MemTotal']}
    arguments = docopt(helpstr)

    processes = int(arguments['--processes'])
    procs = []
    memory_pct = float(arguments['--memory'] or 100.0)

    try:
        # Start a memory-load process.
        if memory_pct > 0:
            print ("Starting a process to load %s%% of memory. PID:" % memory_pct),
            # Approximate. Sue me.
            rng = (proc_meminfo['MemTotal'] * (memory_pct / 100.0)) / 32
            code = "a = range(%d);raw_input()" % rng
            args = [
                # 'exec' causes the command to inherit the shell process.
                # Without it, the shell would start a child process with a
                # different PID and which we could not .kill()
                "exec",
                sys.executable, '-c', '"%s"' % code
            ]
            proc = subprocess.Popen(" ".join(args), shell=True)
            procs.append(proc)
            print proc.pid, "loaded."

        # Start CPU-load processes.
        if processes:
            print ("%d processors." % cpu_count)
            for p in xrange(processes):
                which_cpu = p % cpu_count
                print ("Starting a process to load processor %d. PID:" % which_cpu),
                args = [
                    # 'exec' causes the command to inherit the shell process.
                    # Without it, the shell would start a child process with a
                    # different PID and which we could not .kill()
                    "exec",
                    'taskset',
                    '-c', str(which_cpu),
                    sys.executable, '-c', '"while True: pass"'
                ]
                proc = subprocess.Popen(" ".join(args), shell=True)
                procs.append(proc)
                print ("%d," % proc.pid),
                print "loaded."

        raw_input("Hit 'Enter' to stop loadit.")
    finally:
        print "Shutting down..."
        for proc in procs:
            proc.kill()
        for proc in procs:
            print "Process with PID", proc.pid, "...",
            proc.wait()
            print "killed."
        print "Done."


if __name__ == '__main__':
    main()
