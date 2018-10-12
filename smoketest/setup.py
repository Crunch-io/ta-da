from setuptools import setup, find_packages
import os
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(this_dir, 'README.rst')) as f:
    README = f.read()
del f


setup(
    author=u'Crunch.io',
    author_email='dev@crunch.io',
    description='Crunch Smoke Test Suite',
    license='Proprietary',
    long_description=README,
    name='cr.smoketest',
    namespace_packages=['cr'],
    packages=find_packages(),
    include_package_data=True,
    version='0.0.1',
    zip_safe=False,
    install_requires=[
        'docopt',
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
            'cr.smoketest=cr.smoketest.__main__:main',
        ],
    },
)
