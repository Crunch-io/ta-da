About crhosts
-------------------------

crhosts is a Python package to make connecting to Crunch servers easier.

Usage
-----

Run with `--help` to see usage.
You might want to refer to help of each specific Command
for guidance. The only general option you are interested
in it's probably ``-e alpha`` which will work against
``alpha`` environment instead of production one.

Commands
--------

tags
~~~~

Lists all available kind of servers in our infrastructure::

  (venv)Pulsar:crhosts amol$ crhosts tags
       searchservers
       None
       jupyter
       webservers
       dbservers
       logservers
       zz9servers
       vpc-nat
       redisservers
       jenkins

list
~~~~

Lists all servers existing for a specific tag::

  (venv)Pulsar:crhosts amol$ crhosts list webservers
       0 eu-backend-3-155.priveu.crunch.io
       1 eu-backend-4-189.priveu.crunch.io

connect
~~~~~~~

Connect to a specified server out of those listed by ``tag`` command::

  (venv)Pulsar:crhosts amol$ crhosts connect webservers 0
  Connecting to eu-backend-3-155.priveu.crunch.io
  Last login: Mon Sep 24 10:22:39 2018 from ip-10-30-0-4.eu-west-1.compute.internal
  [root@eu-backend-3-155 ~]# 

admin
~~~~~

Opens the Admin Web Interface for the specified environment::

  (venv)Pulsar:tools amol$ crhosts -e alpha admin
  Connecting to alpha-backend-4-212.priveu.crunch.io

