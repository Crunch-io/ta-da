#!/bin/bash

INDEX_PROCS=40
TOTAL_DATASETS=`mongo io_crunch_db --quiet --eval 'db.datasets.count({"version": "master__tip"})'`
DATASET_CHUNK_SIZE=$((TOTAL_DATASETS / INDEX_PROCS))

echo "Datasets:" $TOTAL_DATASETS
echo "Chunk size:"  $DATASET_CHUNK_SIZE

LOG_DIR=/home/centos/logs
ZZ9_REPO=/remote_prod/eu/zz9repo

CRUNCH_IO_DIR=/var/lib/crunch.io
INDEX_COMMAND=$CRUNCH_IO_DIR/venv/bin/cr.index
SERVER_SETTINGS=$CRUNCH_IO_DIR/cr.server-00.conf
ALIAS=edge_ngrams

for i in $(seq 0 $INDEX_PROCS);
do
    OFFSET=$(($i * $DATASET_CHUNK_SIZE))
    CR_LOGLEVEL=1 nohup $INDEX_COMMAND $SERVER_SETTINGS --repo=$ZZ9_REPO --alias=$ALIAS --offset=$OFFSET --limit=$DATASET_CHUNK_SIZE --skip-existing > $LOG_DIR/cr.index.$ALIAS.$OFFSET.log &
done