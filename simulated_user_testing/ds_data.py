#!/usr/bin/env python3
"""
Big Dataset data helper script

Usage:
    ds_data.py list-datasets [options] [--projects] [--project=PROJECT]
    ds_data.py upload-chunks [options] <chunk-data-file>...
    ds_data.py append-sources [options] <input-file> <dataset-id>

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -i                      Run interactive prompt after executing command
    -v                      Print verbose messages
    --timeout=SECONDS       [default: 3600]

Commands:
    list-datasets
        Print list of datasets (tests pycrunch connection)
    upload-chunks
        Create a Source from each <chunk-data-file>
        Print one Source URL per line to stdout
        The data files were previously downloaded by ds_meta.py
    append-sources
        Append to dataset each source listed in <input-file>,
        One Source HTTP URL per line.
"""
from __future__ import print_function
import os
import sys

import docopt
import yaml
import six
from six.moves.urllib import parse as urllib_parse

from crunch_util import connect_pycrunch, wait_for_progress


def do_list_datasets(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    verbose = args["-v"]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    if args["-i"]:
        import IPython

        IPython.embed()
    if args["--projects"]:
        for proj in six.itervalues(site.projects.index):
            print(u"{proj.id} {proj.name}".format(proj=proj))
        return 0
    if args["--project"]:
        proj_name_or_id = args["--project"]
        try:
            proj = site.projects.by("id")[proj_name_or_id]
        except KeyError:
            proj = site.projects.by("name")[proj_name_or_id]
        url = urllib_parse.urljoin(proj.entity_url, "datasets/")
        response = site.session.get(url)
        datasets_index = response.json()["index"]
        for ds_info in six.itervalues(datasets_index):
            print(u"{ds[id]} {ds[name]}".format(ds=ds_info))
        return 0
    for ds in six.itervalues(site.datasets.index):
        print(u"{ds.id} {ds.name}".format(ds=ds))
    return 0


def do_upload_chunks(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    verbose = args["-v"]
    chunk_filenames = args["<chunk-data-file>"]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    for filename in chunk_filenames:
        if verbose:
            print("Creating source from file {}".format(filename), file=sys.stderr)
        with open(filename, "rb") as f:
            # TODO: detect and handle non-CSV data chunks?
            content_type = "text/csv"
            # Detect if chunk is gzipped
            ext = os.path.splitext(filename)[1]
            if not ext:
                magic = f.read(2)
                f.seek(0)
                if magic == b"\x1f\x8b":
                    ext = ".gz"
            if ext == ".gz":
                file_info = (
                    os.path.basename(filename),
                    f,
                    content_type,
                    {"Content-Encoding": "gzip"},
                )
            else:
                file_info = (os.path.basename(filename), f, content_type)
            response = site.session.post(
                site.sources.self, files={"uploaded_file": file_info}
            )
            response.raise_for_status()
            if verbose:
                print(response, file=sys.stderr)
            source_url = response.headers["Location"]
            print(source_url)


def do_append_sources(args):
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)[args["-p"]]
    verbose = args["-v"]
    timeout = float(args["--timeout"])
    filename = args["<input-file>"]
    dataset_id = args["<dataset-id>"]
    site = connect_pycrunch(config["connection"], verbose=verbose)
    dataset_url = "{}{}/".format(site.datasets.self, dataset_id)
    ds = site.session.get(dataset_url).payload
    with open(filename) as f:
        for line in f:
            source_url = line.strip()
            if not source_url:
                continue
            if not validate_url(source_url):
                raise AssertionError("Invalid source URL: {}".format(source_url))
            if verbose:
                print(
                    "Appending", source_url, "to dataset", dataset_id, file=sys.stderr
                )
            response = ds.batches.post(
                {"element": "shoji:entity", "body": {"source": source_url}}
            )
            if wait_for_progress(
                site, response, timeout_sec=timeout, verbose=verbose, retry_delay=0.125
            ):
                if verbose:
                    print("Finished appending to dataset", ds.body.id, file=sys.stderr)
            else:
                raise Exception("Timed out appending to dataset {}".format(ds.body.id))


def validate_url(url):
    """Return True if it looks like a real HTTP URL, False otherwise"""
    p = urllib_parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        return False
    if (not p.netloc) or (" " in p.netloc):
        return False
    if (not p.path) or (" " in p.path):
        return False
    try:
        p.port
    except ValueError:
        return False
    return True


def main():
    args = docopt.docopt(__doc__)
    if args["list-datasets"]:
        return do_list_datasets(args)
    elif args["upload-chunks"]:
        return do_upload_chunks(args)
    elif args["append-sources"]:
        return do_append_sources(args)
    else:
        raise NotImplementedError("Sorry, that command is not yet implemented.")


if __name__ == "__main__":
    sys.exit(main())
