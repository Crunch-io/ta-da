"""
Common library for operations using the Crunch API
"""
from __future__ import print_function
from collections import OrderedDict
from contextlib import contextmanager
import codecs
import copy
from datetime import datetime
import gzip
import io
import itertools
import json
import os
import shutil
import sys
import tempfile
import time
import warnings

import pycrunch
import pycrunch.progress
import six
from six.moves.urllib import parse as urllib_parse
import urllib3.exceptions

# Certificate for local.crunch.io has no `subjectAltName`, which causes warnings
# See  https://github.com/shazow/urllib3/issues/497 for details.
warnings.simplefilter("ignore", urllib3.exceptions.SubjectAltNameWarning)

# Turn off warnings if server certificate validation is turned off.
warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)


try:
    TimeoutError
except NameError:
    # Python 2 doesn't have TimeoutError built in
    class TimeoutError(OSError):
        pass


def connect_pycrunch(connection_info, verbose=False):
    """
    connection_info: dictionary containing connection parameters:
        api_url: URL of the Crunch API
        token: If given, used for token authentication
        username, password: Supply these for password authentication
        cert: Passed through to requests library if given
        progress_timeout: Number of seconds to wait before giving up
        progress_interval: Number of seconds to sleep between retries
    Return:
        a pycrunch.shoji.Catalog "site" object. It has a session attribute that
        is derived from requests.sessions.Session, which can be used for making
        HTTP requests to the API server.
    """
    api_url = connection_info["api_url"]
    progress_timeout = float(
        connection_info.get(
            "progress_timeout", pycrunch.progress.DEFAULT_PROGRESS_TIMEOUT
        )
    )
    progress_interval = float(
        connection_info.get(
            "progress_interval", pycrunch.progress.DEFAULT_PROGRESS_INTERVAL
        )
    )
    progress_tracking = pycrunch.progress.DefaultProgressTracking(
        timeout=progress_timeout, interval=progress_interval
    )
    if connection_info.get("token"):
        if verbose:
            print("Connecting to", api_url, "using token.", file=sys.stderr)
        session = pycrunch.Session(
            token=connection_info["token"],
            domain=urllib_parse.urlparse(api_url).netloc,
            progress_tracking=progress_tracking,
        )
    else:
        if verbose:
            print(
                "Connecting to",
                api_url,
                "as",
                connection_info["username"],
                file=sys.stderr,
            )
        session = pycrunch.Session(
            email=connection_info["username"],
            password=connection_info["password"],
            progress_tracking=progress_tracking,
        )
    # If this session hook is not installed, you get an error from lemonpy.py:
    # AttributeError: No handler found for response status 301
    # This happens on alpha but not on a local dev VM.
    session.hooks["response"].status_301 = lambda r: r
    try:
        response = session.get(
            api_url,
            verify=connection_info.get("verify", False),
            cert=connection_info.get("cert"),
        )
    except Exception as err:
        sanitized_connection_info = connection_info.copy()
        if "password" in sanitized_connection_info:
            sanitized_connection_info["password"] = "*****"
        msg = (
            "Error getting Crunch API session: {err}\n"
            "API URL: {api_url}\n"
            "Connection info: {sanitized_connection_info}"
        ).format(
            err=err,
            api_url=api_url,
            sanitized_connection_info=sanitized_connection_info,
        )
        raise Exception(msg)
    site = response.payload
    return site


def get_dataset_by_id(site, dataset_id):
    """
    Return the pycrunch.shoji.Entity object corresponding to the dataset ID

    This function does the same thing as site.datasets.by('id')[ds_id].entity
    except that it can also access datasets outside of the user's personal
    project.

    site:
        pycrunch.shoji.Catalog object returned by connect_pycrunch()
    dataset_id:
        ID of the dataset to fetch
    """
    dataset_url = "{}{}/".format(site.datasets.self, dataset_id)
    return site.session.get(dataset_url).payload


def create_dataset(
    site,
    metadata,
    dataset_name=None,
    timeout_sec=300.0,
    retry_delay=0.25,
    verbose=False,
):
    """
    Create a new dataset with just metadata, no rows of data yet.
    site:
        pycrunch.shoji.Catalog object returned by connect_pycrunch()
    metadata:
        A filename or dict or file object containing dataset metadata.
    dataset_name:
        If metadata is a dict and this parameter is not None or empty string,
        use it to override the dataset name in metadata.
    """
    if verbose:
        print("Creating dataset...", file=sys.stderr)
    post_url = site.datasets.self
    headers = {"Content-Type": "application/json"}
    if isinstance(metadata, six.string_types):
        metadata_filename = metadata
        f = open(metadata_filename, "rb")
    elif isinstance(metadata, dict):
        metadata_filename = "-"
        if dataset_name:
            metadata = copy.deepcopy(metadata)
            metadata["body"]["name"] = dataset_name
        f = io.BytesIO(json.dumps(metadata).encode("utf-8"))
    else:
        # Assume metadata is a file-like object
        f = metadata
        metadata_filename = f.name
    try:
        if metadata_filename.endswith(".gz"):
            headers["Content-Encoding"] = "gzip"
        t0 = datetime.utcnow()
        r = site.session.post(post_url, data=f, headers=headers)
    finally:
        f.close()
    r.raise_for_status()
    dataset_url = r.headers["Location"]
    if r.status_code == 202:
        if not wait_for_progress(
            site, r, timeout_sec=600.0, retry_delay=0.25, verbose=verbose
        ):
            msg = (
                "Timed out creating dataset\n"
                "POST URL: {post_url}\n"
                "Dataset URL: {dataset_url}\n"
                "Request originally sent at {t0} UTC"
            ).format(dataset_url=dataset_url, post_url=post_url, t0=t0)
            raise TimeoutError(msg)
    ds = site.session.get(dataset_url).payload
    if verbose:
        print("Created dataset", ds.body.id, file=sys.stderr)
    return ds


def create_dataset_from_csv(
    site,
    metadata,
    fileobj_or_url,
    dataset_name=None,
    timeout_sec=300.0,
    retry_delay=0.25,
    verbose=False,
):
    """
    site:
        pycrunch.shoji.Catalog object returned by connect_pycrunch()
    metadata:
        A filename or dict or file object containing dataset metadata.
    fileobj_or_url:
        If a string, a URL pointing to the CSV data. The URL must be
        accessible from the Crunch server. If None, don't create the data,
        just the metadata. Otherwise, a file-like object open for reading
        (binary), containing CSV data compatible with the metadata. For CSV
        data greater than 100MB, pass None and then follow up with a call to
        append_csv_file_to_dataset().
    dataset_name:
        If metadata is a dict and this parameter is not None or empty string,
        use it to override the dataset name in metadata.
    See:
        http://docs.crunch.io/feature-guide/feature-importing.html#example
        http://docs.crunch.io/_static/examples/dataset.json
        http://docs.crunch.io/_static/examples/dataset.csv
    Poll the progress URL to make sure the upload is complete.
    Return the dataset entity
    """
    ds = create_dataset(
        site,
        metadata,
        dataset_name=dataset_name,
        timeout_sec=timeout_sec,
        retry_delay=retry_delay,
        verbose=verbose,
    )
    append_csv_file_to_dataset(
        site,
        ds,
        fileobj_or_url,
        timeout_sec=timeout_sec,
        retry_delay=retry_delay,
        verbose=verbose,
    )
    return ds


def append_csv_file_to_dataset(
    site,
    ds,
    file_obj_or_name_or_url,
    timeout_sec=300.0,
    retry_delay=0.25,
    verbose=False,
):
    """
    Append a CSV file to an existing dataset. The CSV file must be compatible
    with the existing dataset metadata.
    site:
        pycrunch.shoji.Catalog object returned by connect_pycrunch()
    ds:
        A dataset as returned by site.datasets.create() or by
        site.datasets.by('id')[ds_id].entity or by
        get_dataset(site, dataset_id)
    file_obj_or_name_or_url:
        File-like object (perhaps a temp file) containing <= 100MB CSV data,
        or name of local file containing <= 100MB CSV data,
        or an HTTP URL which can point to > 100MB CSV data.
    """
    if verbose:
        print("Dataset URL:", ds.self, file=sys.stderr)

    def _post_fileobj(filename, f):
        return site.session.post(
            site.sources.self,
            files={"uploaded_file": (os.path.basename(filename), f, "text/csv")},
        )

    if isinstance(file_obj_or_name_or_url, six.string_types):
        p = urllib_parse.urlparse(file_obj_or_name_or_url)
        if p.scheme and p.netloc:
            data_url = file_obj_or_name_or_url
            if verbose:
                print("Creating source from URL {}".format(data_url), file=sys.stderr)
            response = site.sources.post(
                {
                    "element": "shoji:entity",
                    "body": {
                        "location": data_url,
                        "description": "Source created from URL {}".format(data_url),
                    },
                }
            )
        else:
            filename = file_obj_or_name_or_url
            if verbose:
                print("Creating source from file:", filename, file=sys.stderr)
            with open(filename, "rb") as f:
                response = _post_fileobj(filename, f)
    else:
        f = file_obj_or_name_or_url
        if verbose:
            print("Creating source from file object:", f, file=sys.stderr)
        # temp filename could be an integer
        filename = str(getattr(f, "name", "dataset.csv"))
        response = _post_fileobj(filename, f)

    response.raise_for_status()
    source_url = response.headers["Location"]
    if verbose:
        print("Source created with URL:", source_url, file=sys.stderr)
        print("Appending batch", file=sys.stderr)
    t0 = datetime.utcnow()
    response = ds.batches.post(
        {"element": "shoji:entity", "body": {"source": source_url}}
    )
    if wait_for_progress(site, response, timeout_sec, retry_delay, verbose=verbose):
        if verbose:
            print("Finished appending to dataset", ds.body.id, file=sys.stderr)
    else:
        msg = (
            "Timed out appending to dataset {ds.body.id} after {timeout_sec} seconds\n"
            "POST URL: {ds.batches.self}\n"
            "Source URL in POST body: {source_url}\n"
            "Request originally sent at {t0} UTC"
        ).format(ds=ds, source_url=source_url, timeout_sec=timeout_sec, t0=t0)
        raise TimeoutError(msg)


@contextmanager
def stream_and_compress_json(obj, use_tempfile=False):
    """
    Convert obj to JSON and stream it as a file, compressing it on the way.
    If use_tempfile is true, use temporary files to save RAM, cleaning them up
    automatically (about 4 to 5 times slower for large objects.)

    This context manager yields a binary file-like object open for reading.
    """
    if use_tempfile:
        with stream_and_compress_json_with_backing_tempfiles(obj) as f:
            yield f
        return

    # Serialize to JSON, then encode to UTF-8 bytes
    f1 = io.BytesIO(json.dumps(obj).encode("utf-8"))
    f2 = None
    try:
        # Set f2 to a file containing the compressed UTF-8 bytes
        f2 = io.BytesIO()
        with gzip.GzipFile(mode="wb", fileobj=f2) as g:
            shutil.copyfileobj(f1, g)
        f1.close()
        f2.seek(0)

        # Yield the compressed JSON byte stream
        yield f2

        # All done, cleanup in finally block
    finally:
        f1.close()
        if f2 is not None:
            f2.close()


@contextmanager
def stream_and_compress_json_with_backing_tempfiles(obj):
    """
    Like stream_and_compress_json(), only uses tempfiles instead of
    big strings and io.BytesIO objects, to save RAM. 4 to 5 times slower
    on big objects.
    """
    f1 = None  # the object serialized to JSON text
    f2 = None  # the JSON text converted to UTF-8 bytes (on Python 3+)
    f3 = None  # the UTF-8 bytes compressed using gzip
    try:
        # Set up file f1 that will hold JSON text
        params = {"prefix": "tmp-", "suffix": ".json", "delete": False}
        if six.PY2:
            params["mode"] = "w+b"
        else:
            params["mode"] = "w+t"
            params["encoding"] = "utf-8"
        f1 = tempfile.NamedTemporaryFile(**params)

        # Serialize to JSON
        json.dump(obj, f1)

        # Set f2 to a file containing the JSON text as UTF-8 bytes
        if six.PY2:
            f1.seek(0)
            f2 = f1
        else:
            f1.close()
            f2 = open(f1.name, "rb")

        # Set f3 to a file containing the compressed UTF-8 bytes
        f3 = gzip.open(f2.name + ".gz", "wb")
        shutil.copyfileobj(f2, f3)
        f2.close()
        f3.close()
        f3 = open(f3.name, "rb")

        # Yield the compressed JSON byte stream
        yield f3

        # All done, cleanup in finally block
    finally:
        for f in (f1, f2, f3):
            if f is not None:
                try:
                    f.close()
                    os.remove(f.name)
                except BaseException:
                    pass


def test_stream_and_compress_json():
    print("\nstream_and_compress_json: Testing on PY2?", six.PY2)
    d = {"a": 1, "b": 2, "c": [123.5, True, False, None, {"answer": u"s\u00ed"}]}
    with stream_and_compress_json(d) as f:
        assert isinstance(f, io.BytesIO)
        with gzip.GzipFile(mode="rb", fileobj=f) as g:
            assert json.load(g) == d

    # Try again with tempfile
    with stream_and_compress_json(d, use_tempfile=True) as f:
        with gzip.GzipFile(mode="rb", fileobj=f) as g:
            assert json.load(g) == d
    # Check cleanup
    assert f.closed
    assert not os.path.exists(f.name)


def maybe_uncompress_and_load_json(fileobj):
    """
    fileobj: A seekable file-like object opened for binary reading
    Return the JSON object read from that stream, decompressing if necessary
    """
    p = fileobj.tell()
    magic = fileobj.read(2)
    fileobj.seek(p)  # rewind to original position
    if magic == b"\x1f\x8b":
        # It's gzip format
        fileobj = gzip.GzipFile(mode="rb", fileobj=fileobj)
    if not six.PY2:
        fileobj = codecs.EncodedFile(fileobj, "utf-8")
    return json.load(fileobj)


def test_maybe_uncompress_and_load_json_gzipped():
    print("\nmaybe_compress_and_load_json - gzipped: Testing on PY2?", six.PY2)
    d = {"a": 1, "b": 2, "c": [123.5, True, False, None, {"answer": u"s\u00ed"}]}
    f = io.BytesIO()
    with gzip.GzipFile(mode="wb", fileobj=f) as g:
        g.write(json.dumps(d).encode("utf-8"))
    assert f.tell() > 2
    f.seek(0)
    assert f.read(2) == b"\x1f\x8b"  # gzip magic marker
    f.seek(0)
    assert maybe_uncompress_and_load_json(f) == d


def test_maybe_uncompress_and_load_json_uncompressed():
    print("\nmaybe_compress_and_load_json - uncompressed: Testing on PY2?", six.PY2)
    d = {"a": 1, "b": 2, "c": [123.5, True, False, None, {"answer": u"s\u00ed"}]}
    f = io.BytesIO(json.dumps(d).encode("utf-8"))
    assert f.read(1) == b"\x7b"  # left curly brace
    f.seek(0)
    assert maybe_uncompress_and_load_json(f) == d


def create_dataset_from_csv2(
    site,
    metadata,
    fileobj_or_url,
    timeout_sec=300.0,
    retry_delay=None,
    verbose=False,
    dataset_name=None,
    gzip_metadata=True,
):
    """
    site:
        pycrunch.shoji.Catalog object returned by connect_pycrunch()
    metadata:
        A dict containing dataset metadata.
    fileobj_or_url:
        If a string, a URL pointing to the CSV data. The URL must be
        accessible from the Crunch server. If None, don't create the data,
        just the metadata. Otherwise, a file-like object open for reading
        (binary), containing CSV data compatible with the metadata. For CSV
        data greater than 100MB, pass None and then follow up with a call to
        append_csv_file_to_dataset().
    dataset_name:
        If not None, override dataset name in metadata. (Default is None.)
    gzip_metadata:
        If true (the default), gzip the metadata in the JSON request body.
    See:
        http://docs.crunch.io/feature-guide/feature-importing.html#example
        http://docs.crunch.io/_static/examples/dataset.json
        http://docs.crunch.io/_static/examples/dataset.csv
    Poll the progress URL to make sure the upload is complete.
    Return the dataset entity
    """
    if verbose:
        print("Creating dataset", file=sys.stderr)
    if dataset_name is not None:
        metadata = copy.deepcopy(metadata)
        metadata["body"]["name"] = dataset_name
    if gzip_metadata:
        with stream_and_compress_json(metadata) as f:
            # We have to call site.session.post() or else pycrunch tries to be
            # overly helpful and re-do the JSON serialization.
            response = site.session.post(
                site.datasets.self,
                data=f,
                headers={
                    "Content-Type": "application/json",
                    "Content-Encoding": "gzip",
                },
                stream=True,
            )
        ds_url = wait_for_progress2(
            site, response, timeout_sec, retry_delay=retry_delay, verbose=verbose
        )
        ds = site.session.get(ds_url).payload
    else:
        ds = site.datasets.create(metadata).refresh()
    if fileobj_or_url is not None:
        if isinstance(fileobj_or_url, six.string_types):
            data_url = fileobj_or_url
            response = site.session.post(
                ds.batches.self,
                json={"element": "shoji:entity", "body": {"url": data_url}},
                headers={"Content-Type": "application/shoji"},
            )
        else:
            data_fileobj = fileobj_or_url
            filename = getattr(data_fileobj, "name", "dataset.csv")
            response = site.session.post(
                ds.batches.self, files={"file": (filename, data_fileobj, "text/csv")}
            )
        wait_for_progress2(
            site, response, timeout_sec, retry_delay=retry_delay, verbose=verbose
        )
    if verbose:
        print("Created dataset", ds.body.id, file=sys.stderr)
    return ds


def exponential_interval_generator(starting_delay):
    """
    Generate delay values in seconds, each twice as big as the previous.
    """
    while True:
        yield starting_delay
        starting_delay *= 2


def table_interval_generator(delay_count_table=None):
    """
    Generate retry interval values in seconds using a lookup table.
    If table is not given, use this default:
    - Every 0.25 seconds * 4
    - Every 1.0 seconds * 20
    - Every 2.0 seconds * 20
    - Every 10.0 seconds * 30
    - Every 30.0 seconds * 60
    - Every 60.0 seconds * 60
    - Every 300.0 seconds * forever
    """
    if delay_count_table is None:
        delay_count_table = [
            (0.25, 4),
            (1.0, 20),
            (2.0, 20),
            (10.0, 30),
            (30.0, 60),
            (60.0, 60),
            (300.0,),
        ]
    for delay in itertools.chain(
        *(itertools.repeat(*args) for args in delay_count_table)
    ):
        yield delay


def wait_for_progress(
    site, progress_response, timeout_sec, retry_delay=None, verbose=False
):
    """
    Wait for an API call to finish that returned a progress response.
    site: The result of calling connect_pycrunch()
    progress_response: The result of posting to an API that returns progress.
    timeout_sec: Total seconds to wait for API call completion.
    retry_delay: Starting seconds between polling progress endpoint
    Return True if progress finishes, False if it times out.
    """
    progress_response.raise_for_status()
    progress_url = progress_response.json()["value"]
    if verbose:
        print("Waiting on progress URL ...", file=sys.stderr)
    progress_amount = None
    if isinstance(retry_delay, (int, float)):
        retry_delay_generator = exponential_interval_generator(retry_delay)
    elif retry_delay is None:
        retry_delay_generator = table_interval_generator()
    else:
        raise TypeError("Invalid retry_delay")
    t0 = t = time.time()
    while t - t0 <= timeout_sec:
        response = site.session.get(progress_url)
        response.raise_for_status()
        progress = response.json()["value"]
        if verbose:
            print(progress, file=sys.stderr)
        progress_amount = progress.get("progress")
        if progress_amount in (100, -1, None):
            return True
        next_t = t + next(retry_delay_generator)
        t = time.time()
        if t < next_t:
            time.sleep(next_t - t)
            t = time.time()
    else:
        if verbose:
            print("Timeout after", timeout_sec, "seconds.", file=sys.stderr)
        return False


def wait_for_progress2(
    site, progress_response, timeout_sec, retry_delay=None, verbose=False
):
    """
    Wait for an API call to finish that may return either a 201 or 202 response.

    site: The result of calling connect_pycrunch()
    progress_response: The response object returned by posting.
    timeout_sec: Total seconds to wait for API call completion.
    retry_delay: Starting seconds between polling progress endpoint
    verbose: If true, print messages while polling progress

    If the response status code is initially 201 (Created), immediately return
    resource_url

    Otherwise, get the progress URL out of the response and poll that URL until
    it returns a progress of 100, -1, or None (-1 or None mean error).

    If the final progress is 100, return resource_url.

    If the final progress is -1 or None, raise a pyrcrunch.TaskError exception
    containing the error message returned by the progress API. Also set a
    resource_url attribute on the exception object.

    If timeout_sec seconds pass without the progress API returning a progress
    indicating completion, raise TimeoutError. Also set a resource_url attribute
    on the exception object.
    """
    progress_response.raise_for_status()
    resource_url = progress_response.headers["Location"]
    if progress_response.status_code == 201:  # Created
        return resource_url
    elif progress_response.status_code != 202:  # Accepted
        raise ValueError("progress_response is not a 202 response")
    progress_url = progress_response.json()["value"]
    if verbose:
        print("Waiting on progress API ...", file=sys.stderr)
    if isinstance(retry_delay, (int, float)):
        retry_delay_generator = exponential_interval_generator(retry_delay)
    elif retry_delay is None:
        retry_delay_generator = table_interval_generator()
    else:
        raise TypeError("Invalid retry_delay")
    t0 = t = time.time()
    while t - t0 <= timeout_sec:
        response = site.session.get(progress_url)
        response.raise_for_status()
        progress = response.json()["value"]
        if verbose:
            print(progress, file=sys.stderr)
        progress_amount = progress.get("progress")
        if progress_amount == 100:
            # Successful completion
            return resource_url
        if progress_amount in (-1, None):
            # Error
            msg = {
                "resource_url": resource_url,
                "message": progress.get("message", "<no message returned>"),
            }
            err = pycrunch.TaskError(json.dumps(msg))
            err.resource_url = resource_url
            raise err
        next_t = t + next(retry_delay_generator)
        t = time.time()
        if t < next_t:
            time.sleep(next_t - t)
            t = time.time()
    else:
        if verbose:
            print("Timeout after", timeout_sec, "seconds.", file=sys.stderr)
        msg = {
            "resource_url": resource_url,
            "message": "Timeout after {} seconds".format(timeout_sec),
        }
        err = TimeoutError(json.dumps(msg))
        err.resource_url = resource_url
        raise err


def get_ds_metadata(ds, set_derived_field=True):
    """
    ds: pycrunch dataset returned by site.datasets.by('id')[ds_id].entity
    Return a dictionary containing metadata for this dataset, see:
        http://docs.crunch.io/feature-guide/feature-importing.html#example
    """
    response = ds.session.get(ds.table.self)
    response.raise_for_status()
    table = response.json()
    if "description" in table:
        del table["description"]
    if "self" in table:
        del table["self"]
    result = OrderedDict()
    result["element"] = "shoji:entity"
    result["body"] = body = OrderedDict()
    body["name"] = ds.body["name"]
    body["description"] = ds.body["description"]
    body["table"] = table
    if set_derived_field:
        for var_url, var_info in six.iteritems(ds.variables.index):
            if var_info["derived"]:
                var_id = urllib_parse.urlparse(var_url).path.rsplit("/", 2)[-2]
                table["metadata"][var_id]["derived"] = True
    return result


def get_pk_alias(ds):
    """
    ds: pycrunch dataset returned by site.datasets.by('id')[ds_id].entity
    Return the alias of the PK column, or None if no Primary Key.
    Raise an exception if there are multiple PKs (is that allowed?)
    """
    pk_info = ds.pk
    pk_url_list = pk_info.body.pk
    if not pk_url_list:
        return None
    if len(pk_url_list) > 1:
        raise RuntimeError(
            "Can't handle {} PKs in dataset {}".format(len(pk_url_list), ds.id)
        )
    pk_url = pk_url_list[0]
    response = ds.session.get(pk_url)
    response.raise_for_status()
    pk_alias = response.json()["body"]["alias"]
    return pk_alias


def set_pk_alias(ds, alias):
    """
    ds: pycrunch dataset returned by site.datasets.by('id')[ds_id].entity
    alias: The alias of the variable that will become the Primary Key
    Set the PK column by alias.
    Raise an error if unsuccessful, otherwise return the response.
    """
    v = ds.variables.by("alias")[alias]
    response = ds.session.post(
        ds.pk.self,
        json={"element": "shoji:entity", "body": {"pk": [v.entity_url]}},
        headers={"Content-Type": "application/shoji"},
    )
    response.raise_for_status()
    return response
