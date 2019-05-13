Simulated User Testing
======================

See Pivotal epic "simulated user testing on alpha"

Script Descriptions
-------------------

- ``extractdatasets.py``: Use the Sentry API to extract the IDs of recent problem datasets
- ``movedatasets.py``: Use datasetreplay package to connect to superadmin and bundle a dataset
- ``scan_http_logs.py``: Parse cr.backend log files and save info in sqlite DB
