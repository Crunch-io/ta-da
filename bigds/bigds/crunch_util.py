"""
Common library for operations using the Crunch API
"""
from __future__ import print_function
import copy
import gzip
import io
import json
import os
import time
import warnings

import pycrunch
import six
from six.moves import urllib
from six.moves.urllib import parse as urllib_parse
import urllib3.exceptions

# Certificate for local.crunch.io has no `subjectAltName`, which causes warnings.
# See  https://github.com/shazow/urllib3/issues/497 for details.
warnings.simplefilter('ignore', urllib3.exceptions.SubjectAltNameWarning)

# Turn off warnings if server certificate validation is turned off.
warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)


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
    api_url = connection_info['api_url']
    if connection_info.get('token'):
        if verbose:
            print("Connecting to", api_url, "using token.")
        session = pycrunch.Session(token=connection_info['token'],
                                   domain=urllib.parse.urlparse(api_url).netloc)
    else:
        if verbose:
            print("Connecting to", api_url, "as", connection_info['username'])
        session = pycrunch.Session(connection_info['username'],
                                   connection_info['password'])
    # If this session hook is not installed, you get an error in pycrunch/lemonpy.py:
    # AttributeError: No handler found for response status 301
    # This happens on alpha but not on a local dev VM.
    session.hooks['response'].status_301 = lambda r: r
    response = session.get(api_url,
                           verify=connection_info.get('verify', False),
                           cert=connection_info.get('cert'))
    site = response.payload
    return site


if six.PY2:
    def _StrToBytesFileAdapter(f):
        return f
else:
    class _StrToBytesFileAdapter(object):

        def __init__(self, f):
            self.f = f

        def write(self, s):
            self.f.write(s.encode('utf-8'))

        def close(self):
            self.f.close()


def create_dataset_from_csv(site, metadata, fileobj_or_url, timeout_sec=300.0,
                            retry_delay=0.25, verbose=False, dataset_name=None,
                            gzip_metadata=True):
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
        If true, gzip the metadata in the JSON request body.
        Default is True.
    See:
        http://docs.crunch.io/feature-guide/feature-importing.html#example
        http://docs.crunch.io/_static/examples/dataset.json
        http://docs.crunch.io/_static/examples/dataset.csv
    Poll the progress URL to make sure the upload is complete.
    Return the dataset entity
    """
    if verbose:
        print("Creating dataset")
    if dataset_name is not None:
        metadata = copy.deepcopy(metadata)
        metadata['body']['name'] = dataset_name
    if gzip_metadata:
        with io.BytesIO() as f:
            g = _StrToBytesFileAdapter(gzip.GzipFile(mode='w', fileobj=f))
            json.dump(metadata, g)
            g.close()
            f.seek(0)
            response = site.session.post(
                site.datasets.self,
                data=f,
                headers={'Content-Type': 'application/json',
                         'Content-Encoding': 'gzip'},
            )
        response.raise_for_status()
        ds_url = response.headers['Location']
        ds_id = ds_url.rstrip('/').rpartition('/')[-1]
        ds = site.datasets.by('id')[ds_id]
        ds = ds.fetch()
    else:
        ds = site.datasets.create(metadata).refresh()
    if fileobj_or_url is not None:
        if isinstance(fileobj_or_url, six.string_types):
            data_url = fileobj_or_url
            response = site.session.post(
                ds.batches.self,
                json={
                    "element": "shoji:entity",
                    "body": {
                        "url": data_url
                    }
                },
                headers={'Content-Type': 'application/shoji'}
            )
        else:
            data_fileobj = fileobj_or_url
            filename = getattr(data_fileobj, 'name', 'dataset.csv')
            response = site.session.post(
                ds.batches.self,
                files={
                    'file': (filename, data_fileobj, 'text/csv'),
                },
            )
        _wait_for_batch(site, response, timeout_sec, retry_delay,
                        verbose=verbose)
    if verbose:
        print("Created dataset", ds.body.id)
    return ds


def append_csv_file_to_dataset(site, ds, filename_or_url, timeout_sec=300.0,
                               retry_delay=0.25, verbose=False):
    """
    Append a CSV file to an existing dataset. The CSV file must be compatible
    with the existing dataset metadata.
    site:
        pycrunch.shoji.Catalog object returned by connect_pycrunch()
    ds:
        A dataset as returned by set.datasets.create() or by
        site.datasets.by('id')[ds_id].entity
    filename_or_url:
        Name of file or URL pointing to CSV data. Only works for local files
        less than 100MB in size. For larger files you must pass an HTTP URL.
    """
    if verbose:
        print("Dataset URL:", ds.self)
    p = urllib_parse.urlparse(filename_or_url)
    if p.scheme and p.netloc:
        data_url = filename_or_url
        if verbose:
            print("Creating source from URL {}".format(data_url))
        response = site.sources.post({
            "element": "shoji:entity",
            "body": {
                "location": data_url,
                "description":
                    "Source created from URL {}".format(data_url)
            }
        })
    else:
        filename = filename_or_url
        if verbose:
            print("Creating source from file {}".format(filename))
        with open(filename, 'rb') as f:
            response = site.session.post(
                site.sources.self,
                files={
                    'uploaded_file':
                        (os.path.basename(filename), f, 'text/csv'),
                },
            )
    response.raise_for_status()
    source_url = response.headers['Location']
    if verbose:
        print("Source created with URL:", source_url)
        print("Appending batch")
    response = ds.batches.post({
        "element": "shoji:entity",
        "body": {
            "source": source_url
        }
    })
    _wait_for_batch(site, response, timeout_sec, retry_delay,
                    verbose=verbose)
    if verbose:
        print("Finished appending to dataset", ds.body.id)


def _wait_for_batch(site, batch_response, timeout_sec, retry_delay,
                    verbose=False):
    batch_response.raise_for_status()
    progress_url = batch_response.json()['value']
    t0 = t = time.time()
    if verbose:
        print("Waiting for batch append to complete ...")
    progress_amount = None
    while t - t0 < timeout_sec:
        response = site.session.get(progress_url)
        progress = response.json()['value']
        if verbose:
            print(progress)
        progress_amount = progress.get('progress')
        if progress_amount in (100, -1, None):
            break
        time.sleep(retry_delay)
        retry_delay *= 2
        t = time.time()
    else:
        if verbose:
            print("Timeout after", timeout_sec, "seconds.")