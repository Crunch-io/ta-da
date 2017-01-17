# Kaboom
Load testing for Crunch services

## Installation
This requires Python and the locust module.

    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install locustio

You'll also need to set some environment variables:

    $ export R_TEST_USER=test.user@example.com
    $ export R_TEST_PW=12345

## Running
To run the current version, do:

    $ locust -f r-locust.py --host=https://alpha.crunch.io