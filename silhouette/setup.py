# pragma: no cover
from setuptools import setup, find_packages

setup(
    name='silhouette',
    version='0.1.0',
    author="Robert Brewer, JJ Del Carpio, Charles Waldman",
    author_email="dev@crunch.io",
    packages=find_packages('.'),
    package_dir={'silhouette': 'silhouette'},
    install_requires=[
    ],
    entry_points = {
    }
)
