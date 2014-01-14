#!/usr/bin/env python

import sys, os

from cr.lib import settings, stores
from cr.lib.entities.datasets import Dataset, confirm_dataset_catalog
from cr.lib.entities.roles import DatasetRole
from cr.lib.entities.sources import Source
from cr.lib.entities.users import User

ZZ9_ENDPOINT = os.environ.get("ZZ9_ENDPOINT", "inproc://zz9_crunch-lib-tests")

TEST_SETTINGS = {
    'APP_STORE': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'test_crunch_app',
        'ZZ9': {'host': ZZ9_ENDPOINT, 'map': 'file:///tmp/zz9.map'},
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
        'MAX_SESSION_KEY': 18446744073709551616L,  # 2 << 63
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


def main():
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


if __name__ == '__main__':
    main()
