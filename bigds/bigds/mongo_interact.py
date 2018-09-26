#!/usr/bin/env python
"""
Connect to the configured Mongo app database and start an interactive Python
session for exploring the data.

Usage:
    mongo_interact.py [<config-filename>]

<config-filename> defaults to /var/lib/crunch.io/cr.server-0.conf

HOWTO:
    List all databases: client.database_names()
    List all collections: db.collection_names()
    Get the number of documents in a collection: db.actions.count()
"""
import datetime
import io
import json
import sys

from bson.objectid import ObjectId
from pymongo import MongoClient
import yaml


class BSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return 'mongo-objectid:{}'.format(obj)
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return super(self, BSONEncoder).default(obj)


def dump_doc(doc, fp, **kwargs):
    """
    Dump a Mongo document to a file object.
    doc: a Mongo document as returned by pymongo
    fp: A file-like object opened for writing
    **kwargs: Additional parameters passed through to json.dump()
    ObjectIds are converted to strings in the format: 'mongo-id:<mongo-id>'
    datetime instances are converted to ISO-formatted time strings.
    """
    cls = kwargs.pop('cls', BSONEncoder)
    json.dump(doc, fp, cls=cls, **kwargs)


def dumps_doc(doc, **kwargs):
    """
    Dump a Mongo document to a string in JSON format.
    doc: a Mongo document as returned by pymongo
    **kwargs: Additional parameters passed through to json.dumps()
    ObjectIds are converted to strings in the format: 'mongo-id:<mongo-id>'
    datetime instances are converted to ISO-formatted time strings.
    """
    fp = io.StringIO()
    dump_doc(doc, fp, **kwargs)
    return fp.getvalue()


def main():
    config_filename = '/var/lib/crunch.io/cr.server-0.conf'
    if len(sys.argv) >= 2:
        config_filename = sys.argv[1]
    with open(config_filename) as f:
        config = yaml.safe_load(f)
    mongo_url = config['APP_STORE']['URL']
    client = MongoClient(mongo_url)
    db = client.get_default_database()
    namespace = {
        'client': client,
        'config_filename': config_filename,
        'db': db,
        'dump_doc': dump_doc,
        'dumps_doc': dumps_doc,
        'mongo_url': mongo_url,
    }
    try:
        import IPython
        IPython.start_ipython(argv=[], user_ns=namespace)
    except ImportError:
        import code
        code.interact(local=namespace)


if __name__ == '__main__':
    main()
