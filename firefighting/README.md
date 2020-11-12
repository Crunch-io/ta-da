Firefighting Scripts
====================

- list_hot_datasets.py - Print a list of all of the dataset IDs in ``host_map`` for a given host. Run this on a backend server.
- check_datamaps.py - Looks at the datamaps of one or more datasets and checks for inconsistencies. If the ``--columns`` option is given, read the first few bytes of each column data file to determine which other files should exist. Run in on the zz9 server. It reads the datamap.zz9 file directly.
- fix_datamap.py - Fix certain types of problems with datamaps related to text columns. Imports ``check_datamaps``. **This script modifies the datamap.zz9 file directly!** Run it carefully on the zz9 server, and only if the dataset is not in use.
- drive_fix_datamap.py - Runs on a backend server. Makes a dataset unavailable, retires the dataset, then sends a message via a control file to an instance of ``fix_datamap.py --stream`` running on a zz9 server.
