# Scripts and utility modules using pycrunch

The Python scripts in this directory allow command-line access to a Crunch stack running
locally or in the Alpha environment.  Besides being useful development utilities they
can also serve as examples of using pycrunch.

The ``crunch_util.py`` module contains common code used by multiple scripts.

## Setup

These scripts read connection and authentication info from a config
file in YAML format, named ``config.yaml`` by default. Copy and edit
the ``config.yaml.example`` file in this directory.

These scripts rely on the external requirements in ``requirements.txt``.
To install those dependencies you can run:
```
pip3 install --user -r requirements.txt
```

## Scripts

- ``list_datasets.py``
- ``create_dataset.py``
- ``append_to_dataset.py``

## Example: List datasets

These examples assume you have set up ``config.yaml`` in this directory.

To list the datasets in your local development Crunch stack:
```
./list_datasets.py
```

To list your personal datasets in the Alpha environment:
```
$ ./list_datasets.py -p alpha --personal
```

Use the ``--help`` option to see how to list projects, or list datasets in a particular
project.

## Example: Create a simple dataset

By default, ``create_dataset.py`` will use sample metadata in ``data/dataset.json`` and
sample data in ``data/dataset.csv``. This results in a dataset named "Example dataset"
with 10 variables and 20 rows.

Example:
```
$ ./create_dataset.py
https://local.crunch.io:28443/api/datasets/dbfdbfd4094342a39c3e47814a421968/
```

Use the ``--help`` option to find out how to create a dataset with different metadata
and data, or with metadata but no data rows.

## Example: Append a CSV file to an existing dataset

Use ``./list_datasets.py`` to get the ID of the dataset you want, then run something
like:
```
$ ./append_to_dataset.py dbfdbfd4094342a39c3e47814a421968 data/dataset.csv
```

