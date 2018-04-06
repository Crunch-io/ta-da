from setuptools import setup, find_packages
import os
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(this_dir, 'README.rst')) as f:
    README = f.read()
del f


setup(
    name='bigds',
    version='0.0.1',
    description='Big Dataset Tools',
    long_description=README,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'docopt',
        'lz4',
        'pycrunch',
        'pyyaml',
        'requests',
        'six',
    ],
    extras_require={
        'testing': [
            'ipython<6.0',
            'flake8',
        ],
    },
    entry_points={
        'console_scripts': [
            'ds.meta=bigds.ds_meta:main',
            'ds.data=bigds.ds_data:main',
            'ds.fix=bigds.ds_fix:main',
            'ds.mongo-move=bigds.ds_mongo_move:main',
        ],
    },
)
