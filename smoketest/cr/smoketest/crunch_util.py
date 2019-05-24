"""
Common library for operations using the Crunch API
"""
from __future__ import print_function
from collections import OrderedDict
import copy
import io
import json
import os
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
            print("Connecting to", api_url, "using token.")
        session = pycrunch.Session(
            token=connection_info["token"], domain=urllib.parse.urlparse(api_url).netloc
        )
    else:
        if verbose:
            print("Connecting to", api_url, "as", connection_info["username"])
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
        print("Creating dataset...")
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
        print("Created dataset", ds.body.id)
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
        print("Dataset URL:", ds.self)

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
                print("Creating source from URL {}".format(data_url))
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
                print("Creating source from file:", filename)
            with open(filename, "rb") as f:
                response = _post_fileobj(filename, f)
    else:
        f = file_obj_or_name_or_url
        if verbose:
            print("Creating source from file object:", f)
        # temp filename could be an integer
        filename = str(getattr(f, "name", "dataset.csv"))
        response = _post_fileobj(filename, f)

    response.raise_for_status()
    source_url = response.headers["Location"]
    if verbose:
        print("Source created with URL:", source_url)
        print("Appending batch")
    response = ds.batches.post(
        {"element": "shoji:entity", "body": {"source": source_url}}
    )
    if wait_for_progress(site, response, timeout_sec, retry_delay, verbose=verbose):
        if verbose:
            print("Finished appending to dataset", ds.body.id)
    else:
        raise Exception("Timed out appending to dataset {}".format(ds.body.id))


def wait_for_progress(site, progress_response, timeout_sec, retry_delay, verbose=False):
    """
    Wait for an API call to finish that returned a progress response.
    site: The result of calling connect_pycrunch()
    progress_response: The result of posting to an API that returns progress.
    timeout_sec: Total seconds to wait for API call completion.
    retry_delay: Seconds to wait in between calls to the progress endpoint
    Return True if progress finishes, False if it times out.
    """
    progress_response.raise_for_status()
    progress_url = progress_response.json()["value"]
    t0 = t = time.time()
    if verbose:
        print("Waiting on progress URL ...")
    progress_amount = None
    while t - t0 < timeout_sec:
        response = site.session.get(progress_url)
        response.raise_for_status()
        progress = response.json()["value"]
        if verbose:
            print(progress)
        progress_amount = progress.get("progress")
        if progress_amount in (100, -1, None):
            return True
        time.sleep(retry_delay)
        retry_delay *= 2
        t = time.time()
    else:
        if verbose:
            print("Timeout after", timeout_sec, "seconds.")
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
