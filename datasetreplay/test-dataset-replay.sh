#!/bin/bash -e

skipfile=$1
tracefile=$2

if [ -z "$skipfile" ]; then
   echo 'Call as <script> <skipfile> <tracefile>, where <skipfile> path to the file with datasets that already got played' 1>&2
   exit 1
fi

if [ -z "$tracefile" ]; then
    echo 'Call as <script> <skipfile> <tracefile>, where <tracefile> is a path to the file log of dataset replays' 1>&2
    exit 1
fi

if [ -z "$CRUNCHENV" ]; then
    CRUNCHENV="eu"
fi

echo "Going to $CRUNCHENV"
dataset_id=$(dataset.pick --skipfile=$skipfile --env=$CRUNCHENV)
echo "Picked $dataset_id"
echo "$dataset_id" >> $skipfile

# Replay from 2nd last savepoint, and from last if there is only 1
last_savepoint=$(dataset.savepoints $dataset_id --env=$CRUNCHENV | sed -n 2p)
if [ -z "$last_savepoint" ]; then
   echo "Only had 1 savepoint..."
   last_savepoint=$(dataset.savepoints $dataset_id --env=$CRUNCHENV | head -n 1)
fi
echo "Savepoint $last_savepoint"

dataset.replay $dataset_id $last_savepoint --env=$CRUNCHENV --tracefile=$tracefile --timelimit=1800
echo "Trimming tracefile to last 300 replays"
tempfile=$(mktemp)
tail -n 300 $tracefile > $tempfile
mv $tempfile $tracefile