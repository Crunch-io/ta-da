#!/bin/bash -e
adminreport /dataset_integrity broken --env=eu -k dataset_id -k name --top=10 --slack=db