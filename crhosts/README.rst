About crhosts
-------------------------

crhosts is a Python package to make connecting to Crunch servers easier.

Usage
-----

Run with `--help` to see usage, here is a sample session::

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

  (venv)Pulsar:crhosts amol$ crhosts list webservers
       0 eu-backend-3-155.priveu.crunch.io
       1 eu-backend-4-189.priveu.crunch.io

  (venv)Pulsar:crhosts amol$ crhosts connect webservers 0
  Connecting to eu-backend-3-155.priveu.crunch.io
  Last login: Mon Sep 24 10:22:39 2018 from ip-10-30-0-4.eu-west-1.compute.internal
  [root@eu-backend-3-155 ~]# 
