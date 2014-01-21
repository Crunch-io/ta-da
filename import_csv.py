#!/usr/bin/env python

import sys, os

from cr.lib import settings, stores
from cr.lib.entities.datasets import Dataset, confirm_dataset_catalog
from cr.lib.entities.roles import DatasetRole
from cr.lib.entities.sources import Source
from cr.lib.entities.users import User


from silhouette import trace


TEST_SETTINGS = {
    'APP_STORE': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'test_crunch_app',
        'ZZ9': {#'host': ZZ9_ENDPOINT,
                'map':  "file:///tmp/zz9.map"},
        'UPLOADS_PATH': os.environ.get('UPLOADS_PATH', '/tmp'),
    },
    'USER_STORE': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'test_crunch_users',
    },
    'TOKEN_STORE': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'test_crunch_tokens',
        'SALT': 'random-string!!@@@',
        'MAX_SESSION_KEY': 1<<63,
    },
    'AUTH_STORE': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'test_crunch_auth',
    },
    'MAIL_SETTINGS': {
        'BACKEND': 'dummy',
        'DEFAULT_FROM_ADDRESS': 'noreply@crunch.io'
    }
}


def main(filename, dsname, dsid):
    import cProfile, resource
    def utime():
        return resource.getrusage(0).ru_utime * 1000000

    settings.settings.update(TEST_SETTINGS)

    stores.init()

    user = User.confirm({'email': 'testdb@example.com'})

    DatasetRole.confirm(
        {'code': 'owner'},
        {'name': 'Owner', 'edit': True, 'view': True}
    )

    print "user.id=", user.id

    print "confirming dataset catalog ...",
    confirm_dataset_catalog()
    print "ok"

    print "importing", filename
    #pr = cProfile.Profile() #utime, 1000000)
    #pr.enable()
    import_csv(filename, dsname, dsid, user.id)
    #pr.disable()
    #pr.dump_stats("prof.out")
    print "ok"
    with open('trace.pickle', 'w') as f:
        trace.save(f)

def import_csv(fname, dsname, dsid, userid):
    f = open(fname, 'r')
    source = Source.from_file(f, user_id=userid)
    ds = Dataset(id=dsid, name=dsname, user_id=userid)
    ds.create()
    ds.add_source(source)
    print ds

if __name__ == '__main__':

    if len(sys.argv) != 4 or '-h' in sys.argv:
        print "Usage: %s filename dsname dsid" % sys.argv[0]
        sys.exit(-1)

    fname = sys.argv[1]
    dsname = sys.argv[2]
    dsid = sys.argv[3]

    main(fname, dsname, dsid)
