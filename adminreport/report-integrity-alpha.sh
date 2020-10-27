#!/bin/bash -e
adminreport /dataset_integrity broken --env=alpha -k dataset_id -k name --top=10 --slack=sentry-alpha
