"""
Common library for operations using the Crunch API
"""
from __future__ import print_function
from collections import OrderedDict
import codecs
import copy
import gzip
import io
import itertools
import json
import os
import random
import sys
import time
import warnings

import pycrunch
import pycrunch.shoji
import six
from six.moves import urllib
from six.moves.urllib import parse as urllib_parse
import urllib3.exceptions

# Certificate for local.crunch.io has no `subjectAltName`, which causes warnings
# See  https://github.com/shazow/urllib3/issues/497 for details.
warnings.simplefilter("ignore", urllib3.exceptions.SubjectAltNameWarning)

# Turn off warnings if server certificate validation is turned off.
warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)


def connect_pycrunch(connection_info, verbose=False):
    """
    connection_info:
        dict containing the key 'api_url' for connecting to the Crunch API,
        and also credentials in 'username' and 'password' keys, or a 'token'
        key containing an authentication token. (Optional 'token' and 'cert'
        keys used to pass parameters through to the requests library.)
    Return:
        a pycrunch.shoji.Catalog "site" object. It has a session attribute that
        is derived from requests.sessions.Session, which can be used for making
        HTTP requests to the API server.
    """
    api_url = connection_info["api_url"]
    if connection_info.get("token"):
        if verbose:
            print("Connecting to", api_url, "using token.", file=sys.stderr)
        session = pycrunch.Session(
            token=connection_info["token"], domain=urllib.parse.urlparse(api_url).netloc
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
            connection_info["username"], connection_info["password"]
        )
    # If this session hook is not installed, you get an error from lemonpy.py:
    # AttributeError: No handler found for response status 301
    # This happens on alpha but not on a local dev VM.
    session.hooks["response"].status_301 = lambda r: r
    response = session.get(
        api_url,
        verify=connection_info.get("verify", False),
        cert=connection_info.get("cert"),
    )
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
        r = site.session.post(post_url, data=f, headers=headers)
    finally:
        f.close()
    r.raise_for_status()
    dataset_url = r.headers["Location"]
    if r.status_code == 202:
        if not wait_for_progress(
            site, r, timeout_sec=600.0, retry_delay=0.25, verbose=verbose
        ):
            raise Exception("Timed out creating dataset: {}".format(dataset_url))
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
    response = ds.batches.post(
        {"element": "shoji:entity", "body": {"source": source_url}}
    )
    if wait_for_progress(site, response, timeout_sec, retry_delay, verbose=verbose):
        if verbose:
            print("Finished appending to dataset", ds.body.id, file=sys.stderr)
    else:
        raise Exception("Timed out appending to dataset {}".format(ds.body.id))


class CompressionWrapper:
    """
    Wrap any file-like object opened for binary reading.
    Compress bytes on the fly as they are read.
    Closing this object closes the wrapped file.

    When you iterate on this object, it returns chunks of bytes sized
    roughly around io.DEFAULT_BUFFER_SIZE, instead of the usual file
    behavior of returning strings of bytes ending with ASCII newline.
    """

    mode = "rb"

    @staticmethod
    def open(cls, filename):
        """
        Open the file for binary reading and wrap it with this class.
        If filename ends with ".gz", blindly trust that it is already compressed and
        return the regular fileobj.
        Otherwise, wrap the fileobj with this class and return the wrapped instance.
        """
        f = open(filename, "rb")
        if filename.endswith(".gz"):
            return f
        return cls(f)

    def __init__(self, f, name=None):
        self.f = f
        self.name = name if name else getattr(f, "name", None)
        self._buffer = io.BytesIO()
        self._gzipper = gzip.GzipFile(self.name, mode="wb", fileobj=self._buffer)

    def read(self, size=-1):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        if size is None or size < 0:
            return self.readall()
        return self._read(size)

    def readall(self):
        chunk_size = io.DEFAULT_BUFFER_SIZE
        compressed_chunks = []
        while True:
            data = self._read(chunk_size)
            if not data:
                break
            compressed_chunks.append(data)
        return b"".join(compressed_chunks)

    def _read(self, n):
        result = b""
        while n > 0 and not result:
            # Work until we get *something* in the buffer or exhaust input
            data = self.f.read(n)
            if data:
                self._gzipper.write(data)
                self._gzipper.flush()
            else:
                # Flush remaining buffered compressed data, then stop reading
                self._gzipper.close()
                n = 0
            result = self._buffer.getvalue()
            self._buffer.seek(0)
            self._buffer.truncate()
        return result

    def __iter__(self):
        return self

    def __next__(self):
        data = self._read(io.DEFAULT_BUFFER_SIZE)
        if not data:
            raise StopIteration()
        return data

    def next(self):
        # For Python 2 compatibility
        return self.__next__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._gzipper.close()
        self._buffer.close()
        self.f.close()

    @property
    def closed(self):
        return self.f.closed


def test_compression_wrapper():
    # Compress stream using CompressionWrapper
    original_content = b"abcdef123456\n"
    f1 = io.BytesIO(original_content)
    f2 = CompressionWrapper(f1, "test.txt")
    assert f2.name == "test.txt"  # setting name worked
    compressed_content = f2.read()
    assert compressed_content  # contents not empty
    assert compressed_content != f1.getvalue()  # contents transformed
    assert f1.tell() == len(f1.getvalue())  # input exhausted
    assert f2.read() == b""  # reading after EOF returns empty bytes
    f2.close()
    assert f2.closed
    assert f1.closed  # closing wrapper closes wrapped file
    try:
        f2.read()
    except ValueError:
        pass  # reading after closed is an error
    else:
        raise AssertionError("Expected ValueError when reading closed file")
    # Uncompress and verify contents
    f3 = io.BytesIO(compressed_content)
    g = gzip.GzipFile(mode="rb", fileobj=f3)
    decompressed_content = g.read()
    assert decompressed_content == original_content
    print("Ok")


def test_compression_wrapper_random_data_small_reads():
    # Generate a an amount of data bigger than the default block size,
    # randomized so it's harder to compress.
    original_content = _create_random_bytes(io.DEFAULT_BUFFER_SIZE * 2)
    f1 = io.BytesIO(original_content)
    f2 = CompressionWrapper(f1, "test.txt")
    # Read and compress the data in small pieces
    compressed_parts = []
    read_size = 8
    while True:
        data = f2.read(read_size)
        if data:
            compressed_parts.append(data)
        else:
            break
    _check_compression_wrapper_parts(compressed_parts, original_content)


def _create_random_bytes(num_bytes):
    return "".join(
        chr(random.randrange(32, 128)) for i in six.moves.xrange(num_bytes)
    ).encode("utf-8")


def _check_compression_wrapper_parts(compressed_parts, original_content):
    num_bytes = len(original_content)
    min_bytes = num_bytes + 1
    max_bytes = 0
    total_bytes = 0
    for part in compressed_parts:
        min_bytes = min(min_bytes, len(part))
        max_bytes = max(max_bytes, len(part))
        total_bytes += len(part)
    num_reads = len(compressed_parts)
    ave_bytes = total_bytes / num_reads
    print("Total uncompressed bytes:", num_bytes)
    print("Number of read()/next() calls:", num_reads)
    print("Total compressed bytes read:", total_bytes)
    print("Min. bytes per read:", min_bytes)
    print("Ave. bytes per read:", ave_bytes)
    print("Max. bytes per read:", max_bytes)
    # Uncompress and verify contents
    f3 = io.BytesIO(b"".join(compressed_parts))
    g = gzip.GzipFile(mode="rb", fileobj=f3)
    decompressed_content = g.read()
    assert decompressed_content == original_content
    print("Ok")


def test_compression_wrapper_zero_read():
    # Compress stream using CompressionWrapper
    # Do a zero-byte read, then read the rest
    original_content = b"abcdef123456\n"
    f1 = io.BytesIO(original_content)
    f2 = CompressionWrapper(f1, "test.txt")
    assert f2.read(0) == b""
    compressed_content = f2.read()
    f2.close()
    try:
        f2.read(0)
    except ValueError:
        pass  # Even zero-byte read on closed file is an error
    else:
        raise AssertionError("Expected ValueError when reading closed file")
    # Uncompress and verify contents
    f3 = io.BytesIO(compressed_content)
    g = gzip.GzipFile(mode="rb", fileobj=f3)
    decompressed_content = g.read()
    assert decompressed_content == original_content
    print("Ok")


def test_compression_wrapper_iterator():
    original_content = _create_random_bytes(io.DEFAULT_BUFFER_SIZE * 2)
    f1 = io.BytesIO(original_content)
    f2 = CompressionWrapper(f1, "test.txt")
    # Read and compress the data in small pieces
    compressed_parts = list(f2)
    _check_compression_wrapper_parts(compressed_parts, original_content)


def test_compression_wrapper_context_manager():
    original_content = b"abcdef123456\n"
    f1 = io.BytesIO(original_content)
    with CompressionWrapper(f1, "test.txt") as f2:
        compressed_content = f2.read()
    assert f2.closed
    # Uncompress and verify contents
    f3 = io.BytesIO(compressed_content)
    g = gzip.GzipFile(mode="rb", fileobj=f3)
    decompressed_content = g.read()
    assert decompressed_content == original_content
    print("Ok")


class JSONReader:
    """
    Wrap a JSON-serializable object in a file-like reader.
    If text=True is passed to the constructor (the default) then read()
    calls return strings. If text=False then read() returns UTF-8 bytes.
    """

    def __init__(self, obj, **kwargs):
        self.name = kwargs.pop("name", None)
        text = kwargs.pop("text", True)
        self._iter = json.JSONEncoder(**kwargs).iterencode(obj)
        self.mode = "r"
        self._empty = ""
        if not text:
            self._iter = codecs.iterencode(self._iter, encoding="utf-8")
            self.mode = "rb"
            self._empty = b""

    def read(self, size=-1):
        """
        Like the read() method on a file object, except if size > 0 then more than
        size characters/bytes could be returned.
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
        if size is None or size < 0:
            return self._empty.join(self._iter)
        if size == 0:
            return self._empty
        return next(self._iter, self._empty)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._iter = None

    @property
    def closed(self):
        return self._iter is None


def test_json_reader_text():
    obj = {"a": 1.23, "b": ["one", "two", "three"], "c": {"k1": 12, "k2": None}}
    jr = JSONReader(obj, name="test.json", indent=4, sort_keys=True)
    assert jr.name == "test.json"
    assert jr.read(0) == ""
    chunks = [jr.read(4), jr.read()]
    # Make sure both reads were non-empty
    assert chunks[0]
    assert chunks[-1]
    result = "".join(chunks)
    assert isinstance(result, str)  # text mode by default
    print(result)
    assert json.loads(result) == obj
    assert jr.read() == ""
    assert not jr.closed
    jr.close()
    assert jr.closed
    try:
        jr.read()
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError when reading closed file")


def test_json_reader_binary():
    obj = {"a": 1.23, "b": ["one", "two", "three"], "c": {"k1": 12, "k2": None}}
    jr = JSONReader(obj, name="test.json", text=False, indent=4, sort_keys=True)
    jr.read(0) == b""
    chunks = [jr.read(4), jr.read()]
    # Make sure all reads were non-empty bytes
    for chunk in chunks:
        assert chunk
        assert isinstance(chunk, bytes)
    result = b"".join(chunks)
    print(result)
    assert json.loads(result.decode("utf-8")) == obj
    assert jr.read() == b""


def create_dataset_from_csv2(
    site,
    metadata,
    fileobj_or_url,
    timeout_sec=300.0,
    retry_delay=0.25,
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
        with CompressionWrapper(
            JSONReader(metadata, text=False), name="metadata.json"
        ) as f:
            response = site.session.post(
                site.datasets.self,
                data=f,
                headers={
                    "Content-Type": "application/json",
                    "Content-Encoding": "gzip",
                },
                stream=True,
            )
        response.raise_for_status()
        ds_url = response.headers["Location"]
        ds_id = ds_url.rstrip("/").rpartition("/")[-1]
        ds = site.datasets.by("id")[ds_id]
        ds = ds.fetch()
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
        wait_for_progress(site, response, timeout_sec, retry_delay, verbose=verbose)
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
