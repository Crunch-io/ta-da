# Scripts and utility modules using pycrunch

The Python scripts in this directory allow command-line access to Crunch
from your own computer. Besides being useful development utilities they
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

## Example: List datasets

These examples assume you have set up ``config.yaml`` in this directory.

To list the datasets in your local development Crunch stack:
```
./list_datasets.py
```

To list your personal datasets in the Alpha environment:
```
./list_datasets.py -p alpha --personal
```

## More to come

I (David H) have other example scripts that I plan to add here that also use
``crunch_util.py``:

- ``create_dataset.py``
- ``append_to_dataset.py``
