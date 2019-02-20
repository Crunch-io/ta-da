#!/bin/bash -e

TODAY=`date +%Y-%m-%d`
PASTMONTH=`date -d "$(date +%Y-%m-1) -1 day" +%Y-%m`

skipfileprefix=$1
if [ -z "$skipfileprefix" ]; then
   echo 'Call as <script> <skipfileprefix> <tracefile>, where <skipfileprefix> path to the file with datasets that already got verified today' 1>&2
   exit 1
fi
skipfile="$skipfileprefix-$TODAY"

tracefile=$2
if [ -z "$tracefile" ]; then
    echo 'Call as <script> <skipfileprefix> <tracefile>, where <tracefile> is a path to the file log of dataset replays' 1>&2
    exit 1
fi

if [ -z "$CRUNCHENV" ]; then
    CRUNCHENV="eu"
fi

echo "Cleaning up old skipfiles != $skipfile"
find $skipfileprefix* -type f ! -wholename $skipfile -delete 2>/dev/null || true

echo "Going to $CRUNCHENV"

dataset_id=$(dataset.pick --skipfile=$skipfile --env=$CRUNCHENV)
echo "Picked $dataset_id"
echo "$dataset_id" >> $skipfile

dataset.verify $dataset_id --env=$CRUNCHENV --tracefile=$tracefile
echo "Trimming tracefile to last 1500 checks"
tempfile=$(mktemp)
tail -n 1500 $tracefile > $tempfile
mv $tempfile $tracefile
