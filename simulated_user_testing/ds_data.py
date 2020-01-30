#!/usr/bin/env python3
"""
Big Dataset data helper script

Usage:
    ds_data.py list-datasets [options] [--projects] [--project=PROJECT]
    ds_data.py obfuscate-chunks [options] <metadata-file> <chunk-data-file>...
    ds_data.py upload-chunks [options] <chunk-data-file>...
    ds_data.py append-sources [options] <input-file> <dataset-id>

Options:
    -c CONFIG_FILENAME      [default: config.yaml]
    -p PROFILE_NAME         Profile section in config [default: local]
    -u USER_ALIAS           Key to section inside profile [default: default]
    -i                      Run interactive prompt after executing command
    -v                      Print verbose messages
    --timeout=SECONDS       [default: 36000]

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
import csv
import codecs
from datetime import datetime
import gzip
import os
import sys

import docopt
import yaml
import six
from six.moves.urllib import parse as urllib_parse

from crunch_util import wait_for_progress
from ds_meta import MetadataModel
from sim_util import connect_api


try:
    TimeoutError
except NameError:
    # Python 2 doesn't have TimeoutError built in
    class TimeoutError(OSError):
        pass


def main():
    args = docopt.docopt(__doc__)
    with open(args["-c"]) as f:
        config = yaml.safe_load(f)
    if args["list-datasets"]:
        return do_list_datasets(config, args)
    elif args["upload-chunks"]:
        return do_upload_chunks(config, args)
    elif args["append-sources"]:
        return do_append_sources(config, args)
    elif args["obfuscate-chunks"]:
        return do_obfuscate_chunks(config, args)
    else:
        raise NotImplementedError("Sorry, that command is not yet implemented.")


def do_list_datasets(config, args):
    site = connect_api(config, args)
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


def do_obfuscate_chunks(config, args):
    raise NotImplementedError("TODO: work-in-progress")
    verbose = args["-v"]
    metadata_filename = args["<metadata-file>"]
    chunk_filenames = args["<chunk-data-file>"]
    meta = MetadataModel(verbose=verbose)
    meta.load(metadata_filename)
    alias_map = meta.alias_map
    for chunk_filename in chunk_filenames:
        print("Looking at", chunk_filename)
        with gzip.open(chunk_filename, "rt") as f:
            r = csv.reader(f)
            for line_num, row in enumerate(r, 1):
                if line_num == 1:
                    cur_aliases = [codecs.decode(a, "rot13") for a in row]
                    aliases_not_found = sorted(set(cur_aliases) - set(alias_map))
                    print("Aliases in CSV file but not in metadata:", aliases_not_found)
                    break


def do_upload_chunks(config, args):
    chunk_filenames = args["<chunk-data-file>"]
    verbose = args["-v"]
    site = connect_api(config, args)
    for filename in chunk_filenames:
        if verbose:
            print("Creating source from file {}".format(filename), file=sys.stderr)
        source_url = upload_source(site, filename)
        print(source_url)
        sys.stdout.flush()  # Make sure progress shows up on stdout


def upload_source(site, filename):
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
        source_url = response.headers["Location"]
    return source_url


def do_append_sources(config, args):
    filename = args["<input-file>"]
    source_urls = []
    with open(filename) as f:
        for line in f:
            source_url = line.strip()
            if not source_url:
                continue
            if not validate_url(source_url):
                raise AssertionError("Invalid source URL: {}".format(source_url))
            source_urls.append(source_url)
    verbose = args["-v"]
    timeout = float(args["--timeout"])
    dataset_id = args["<dataset-id>"]
    site = connect_api(config, args)
    dataset_url = "{}{}/".format(site.datasets.self, dataset_id)
    ds = site.session.get(dataset_url).payload
    for i, source_url in enumerate(source_urls, 1):
        if verbose:
            print(
                "({}/{})".format(i, len(source_urls)),
                "Appending",
                source_url,
                "to dataset",
                dataset_id,
                file=sys.stderr,
            )
        print(source_url)
        sys.stdout.flush()  # Make sure progress shows up on stdout
        append_source(
            site, ds, source_url, i, len(source_urls), timeout=timeout, verbose=verbose
        )


def append_source(
    site, ds, source_url, batch_num, num_batches, timeout=3600.0, verbose=False
):
    t0 = datetime.utcnow()
    response = ds.batches.post(
        {"element": "shoji:entity", "body": {"source": source_url}}
    )
    if wait_for_progress(site, response, timeout_sec=timeout, verbose=verbose):
        if verbose:
            print("Finished appending to dataset", ds.body.id, file=sys.stderr)
    else:
        msg = (
            "Timed out after {timeout} seconds\n"
            "Appending batch {batch_num} of {num_batches} to dataset {ds.body.id}\n"
            "POST URL: {ds.batches.self}\n"
            "Source URL in POST body: {source_url}\n"
            "Request originally sent at {t0} UTC"
        ).format(
            ds=ds,
            source_url=source_url,
            batch_num=batch_num,
            num_batches=num_batches,
            timeout=timeout,
            t0=t0,
        )
        raise TimeoutError(msg)


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


if __name__ == "__main__":
    sys.exit(main())
