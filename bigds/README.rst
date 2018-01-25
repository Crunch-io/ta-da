Big Dataset Tools
=================

This project has (or will have) scripts for creating big datasets for
load-testing and performance diagnosis at scale.

I created these scripts because I want to reproduce in a development
environment datasets with the same characteristics as those in production that
are having performance issues.  It's a non-trivial problem, because the size of
the variable metadata alone exceeds the 100MB request body size limit.

Commands planned or implemented include:

- ``ds.meta get``

  - Pull down dataset metadata to JSON file

- ``ds.meta info``

  - Print statistics about dataset metadata in a JSON file:

    - How many categorial variables, how many categories, etc.

- ``ds.meta anonymize``

  - Modify dataset metadata JSON to change names and aliases, while keeping
    them the same length.

- ``ds.meta post``

  - Create empty dataset from metadata JSON produced by ds_meta_get and
    ds_meta_anonymize

- ``ds.data create``

  - Create a CSV file with N rows of random data compatible with metadata JSON.

- ``ds.data append``

  - Append a (potentially very large) CSV file to a dataset via URL.
