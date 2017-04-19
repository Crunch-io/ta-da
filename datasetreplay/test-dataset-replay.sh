#!/bin/bash -e

skipfile=$1

if [ -z "$skipfile" ]; then
   echo 'Call as <script> <skipfile> where <skipfile> path to the file with datasets that already got played' 1>&2
   exit 1
fi

CRUNCHENV="vagrant"

dataset_id=$(dataset.pick --skipfile=$skipfile --env=$CRUNCHENV)
echo "Picked $dataset_id"
echo "$dataset_id" >> $skipfile
dataset.replay $dataset_id --env=$CRUNCHENV --slack