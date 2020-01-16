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

connect to mongodb secondary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Connect to the server that evaluates True for the ``mongodb:secondary``
predicate::

  (venv)Pulsar:crhosts amol$ crhosts connect dbservers mongodb:secondary
  > Checking eu-mongo-2-94.priveu.crint.net
  > Connecting to eu-mongo-2-94.priveu.crint.net
  Last login: Wed Jan 15 16:07:10 2020 from 10.30.0.60
  [centos@eu-mongo-2-94 ~]$ 

connect to mongodb primary
~~~~~~~~~~~~~~~~~~~~~~~~~~

Connect to the server that evaluates True for the ``mongodb:primary``
predicate::

  (venv)Pulsar:zoom amol$ crhosts connect dbservers mongodb:primary
  > Checking eu-mongo-2-94.priveu.crint.net
  > Checking eu-mongo-6-7.priveu.crint.net
  > Checking eu-mongo-7-5.priveu.crint.net
  > Connecting to eu-mongo-7-5.priveu.crint.net
  Last login: Wed Jan 15 16:07:10 2020 from 10.30.0.60
  [centos@eu-mongo-7-5 ~]$ 

connect to ZZ9 host with HOT copy of dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Connect to server that has the hot copy of a zz9 dataset::

  (venv)Pulsar:zoom amol$ crhosts -e alpha connect zz9servers zz9dataset:e8e30ef7be2b4f82a6fe8d5282afab37
  > Checking alpha-zz9-2-122.priveu.crint.net
  > Checking alpha-zz9-247.priveu.crint.net

  >>> Dataset available in /scratch0/zz9data/hot/e8/e8e30ef7be2b4f82a6fe8d5282afab37 at alpha-zz9-247.priveu.crint.net

  > Connecting to alpha-zz9-247.priveu.crint.net
  Last login: Thu Jan 16 15:04:28 2020 from 10.30.0.60
  [centos@alpha-zz9-247 ~]$ 

