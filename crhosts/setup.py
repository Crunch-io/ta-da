from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

version = "0.0.1"

setup(name='crhosts',
      version=version,
      description="Tool to connect to our dynamic set of servers",
      long_description=README,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Alessandro Molina',
      author_email='alessandro@crunch.io',
      url='https://github.com/Crunch-io/tools',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "requests",
        "paramiko"
      ],
      entry_points={
          'console_scripts': [
              'crhosts=crhosts:main',
         ]
      })
