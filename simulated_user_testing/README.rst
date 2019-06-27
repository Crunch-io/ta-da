Simulated User Testing
======================

See Pivotal epic "simulated user testing on alpha"

Notion page: https://www.notion.so/crunch/Simulated-User-Testing-f9dba6b175144b888854625950c187fc

Setup Steps
-----------

Deployment
..........

Copy the code in this directory to /remote/simulated_user_testing on the Alpha system.

Configuration
.............

Create a ``config.yaml`` file in /remote/simulated_user_testing with contents
like this.  Get the the default user (your) login token value by logging in to
the web UI and copying it from your browser cookies. Make up passwords for the
sim-editor-1 and sim-user-1 users; you will set those passwords later::

    profiles:
        prod:
            api_url: 'https://apps.crunch.io/api'
            users:
                default:
                    email: '<your-username>@crunch.io'
                    token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        alpha:
            api_url: 'https://alpha.crunch.io/api'
            users:
                default:
                    email: '<your-username>@crunch.io'
                    token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
                sim-editor-1:
                    username: 'sim-editor-1@crunch.io'
                    password: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
                sim-user-1:
                    username: 'sim-user-1@crunch.io'
                    password: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

Run ``./ds_meta.py -p alpha -v list-datasets`` to verify you can connect to the
Alpha API as the default user.

Run ``./ds_meta.py -p prod -v list-datasets`` to verify you can connect to the
Production API as the default user (this is only used for making copies of
production dataset metadata during setup).

Go to your account page in Alpha superadmin
(https://alpha.superadmin.crint.net/accounts/00001/ for developers) and create the
following users. Uncheck the "Send invite" checkbox when creating each user. Put your own
Crunch email address in the "From email" box since the default support@crunch.io will
result in an error message.

Email:  sim-editor-1@crunch.io
Name:   Sim Editor 1 
Auth:   Password
Role:   advanced

Name:   Sim User 1
Email:  sim-user-1@crunch.io
Auth:   Password
Role:   basic

To set the password for each test user, go to https://alpha.superadmin.crint.net/users/
and search on the (fake) email address of the test user. Click the link to go to that
user's page in superadmin. Click "Generate link". Copy the link that gets generated. Paste
that link into a new incognito browser window and follow the directions. Enter the same
passwords for these users as you put in the ``config.yaml`` file.

Test this new configuration by making sure these commands run without errors.
Of course no datasets will be listed because these users don't have any yet::

    ./ds_meta.py -p alpha -u sim-editor-1 -v list-datasets
    ./ds_meta.py -p alpha -u sim-user-1 -v list-datasets

Go to the Alpha superadmin page at https://alpha.superadmin.crint.net/projects/ and create the
following projects.

- Quad

  - Enter ``sim-editor-1@crunch.io`` for "Owner email"

- Sim Profiles

  - Enter ``sim-editor-1@crunch.io`` for "Owner email"
  - After the project is created, add user ``sim-user-1@crunch.io`` to the project

After creating the "Sim Profiles" project, create a "Previous" sub project in it.

Create a directory: ``/remote/simulated_user_testing/metadata``

Put in this directory a large Profiles dataset payload to use as a template.
Example: ``Profiles-plus-GB-Feb-2019-metadata.json.gz``

Find the ID of the dataset in production that goes with your sample payload.

Copy the scripts in this directory to one of the production backend servers.

On that server, create a directory: ``s3data-gb-plus``

Run this command to download the import files used to populate that dataset::

    ./get_s3_sources.py download <dataset-id> s3data-gb-plus

Copy (by any means necessary) the ``s3data-gb-plus`` directory with its contents
to ``/remote/simulated_user_testing/`` on the Alpha system.

Add these lines to ``config.yaml``::

    dataset_templates:
        gb_plus:
            create_payload: "metadata/Profiles-plus-GB-Feb-2019-metadata.json.gz"
            data_dir: "s3data-gb-plus"

In this case "gb_plus" is the alias for the series of datasets that will be created
from this metadata template file.


Main Scripts
------------

- ``editor_bot.py``: Simulate what a Profiles editor would do to set up a dataset
- ``user_bot.py``: Simulates analysis done by Profiles customers


Helper Scripts/Modules
----------------------

- ``ds_meta.py``: Works with dataset metadata, creates large datasets from template
- ``ds_data.py``: Uploads data to datasets
- ``get_s3_sources.py``: Download contents of Sources related to dataset
- ``crunch_util.py``: Utilities for working with pycrunch
- ``sim_util.py``: Utilities used by multiple scripts in this project
- ``time_*.py``: Performance testing scripts
