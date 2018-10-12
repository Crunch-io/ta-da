Crunch Smoke Test Suite
=======================

"Smoke tests" are tests that are run against a *real* environment, either Alpha
or production. Unless its name begins with ``destructive-``, each smoke test in
this suite is non-destructive, meaning that it does not delete nor or alter any
pre-existing data or metadata in a pre-existing dataset. It may, however, leave
a trace of Actions in the action history (e.g. adding new rows and then deleting
them again.)

The tests use pycrunch and the Crunch API. Other than pycrunch there should be
no dependencies on Crunch code in this test suite. The smoketests can be run
either with Python 2.7 or 3.6+.

Preparing to run smoke tests
----------------------------

Configuration
.............

The smoke tests read a ``config.yaml`` file in the current directory.  This file
needs to contain API credentials for a user that has permissions to create
datasets in the Crunch environment of interest.

In this example ``config.yaml`` file there are two profiles: ``local`` for
connecting to a local dev VM, and ``alpha`` for connecting to the Alpha system::

   local:
       connection:
           username: 'captain@crunch.io'
           password: 'blahblah'
           api_url: 'https://local.crunch.io:8443/api'
           verify: false
   alpha:
       connection:
           email: 'imadeveloper@crunch.io'
           token: 'cacb4a14c3664590970a798dc44a8fa1'
           api_url: 'https://alpha.crunch.io/api'
           verify: false

Test Dataset IDs
................

Collect the IDs of some datasets that you (or your test user) has permission to
read and write. You might want to fork existing datasets to give yourself
permission, as well as give yourself some insurance against altering the
original dataset.

That said, the goal of this smoke test suite is to have at least some tests that
can be safely run against existing, real datasets non-destructively.

The ``pick-random-dataset`` subcommand can be run on a server that has access to
the dataset repository, in order to generate random samples of datasets.


Running smoke tests
-------------------

Run the smoketest script, giving it a subcommand indicating which smoke test to
run, with appropriate parameters such as a dataset ID. For more details, run the
script with ``--help``.

If cr.smoketest has been installed with ``pip``::

   cr.smoketest --help

If running from the source directory (this directory)::

   python -m cr.smoketest --help

