from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

version = "0.0.1"

setup(name='datasetreplay',
      version=version,
      description="",
      long_description=README,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Unknown',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'requests',
          'docopt'
      ],
      entry_points={
          'console_scripts': [
              'dataset.replay=datasetreplay.datasetreplay:main',
              'dataset.pick=datasetreplay.datasetpick:main',
              'dataset.savepoints=datasetreplay.datasetsavepoint:main',
              'crtracefile.report=datasetreplay.crtracefilereport:main',
              'dataset.oldclean=datasetreplay.datasetoldclean:main',
         ]
      }
)
