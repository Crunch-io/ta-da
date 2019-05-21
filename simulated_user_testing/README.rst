Simulated User Testing
======================

See Pivotal epic "simulated user testing on alpha"

Notion page: https://www.notion.so/crunch/Simulated-User-Testing-f9dba6b175144b888854625950c187fc

Script Descriptions
-------------------

Scripts used for research:

- ``scan_http_logs.py``: Parse cr.backend log files and save info in sqlite DB
- ``copy_from_times.py``: Query Dataset.copy_from times for Profiles dataset series

Scripts for moving data (under ``moving-data/``):

- ``extractdatasets.py``: Use the Sentry API to extract the IDs of recent problem datasets
- ``movedatasets.py``: Use datasetreplay package to connect to superadmin and bundle a dataset
