"""
Graph the result of running copy_from_times_query.py

Usage:
    copy_from_times_graph.py <csv-file>
"""
from __future__ import print_function
import csv
from datetime import datetime
import os
import sys

import docopt
import matplotlib

matplotlib.use("agg")  # noqa: E402
import matplotlib.pyplot as plt


def main():
    args = docopt.docopt(__doc__)
    csv_filename = args["<csv-file>"]
    print("Reading", csv_filename)
    with open(csv_filename, "r") as f:
        reader = csv.DictReader(f)
        ds_creation_time = []
        copy_from_timing = []
        for row in reader:
            tx = datetime.strptime(row["creation_time"], "%Y-%m-%d %H:%M:%S.%f")
            ty = float(row["copy_from_timing"])
            ds_creation_time.append(tx)
            copy_from_timing.append(ty)
    fig = plt.figure(figsize=(10.24, 7.68), dpi=100)
    nrows, ncols, axnum = 1, 1, 1
    ax = fig.add_subplot(nrows, ncols, axnum)
    ax.set_title(os.path.splitext(os.path.basename((csv_filename)))[0])
    ax.set_xlabel("Dataset Creation Time")
    ax.set_ylabel("Dataset.copy_from timing in seconds")
    ax.plot(ds_creation_time, copy_from_timing)
    png_filename = os.path.splitext(csv_filename)[0] + ".png"
    print("Writing", png_filename)
    fig.savefig(png_filename)
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
