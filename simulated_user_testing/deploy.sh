#!/bin/bash -e
if [ "$1" = "" -o "$1" = "--help" ] ; then
    echo "Usage: ./deploy.sh <username>@<hostname>:/<directory>/"
    echo "Example: ./deploy.sh centos@alpha-backend-XXX:/remote/simulated_user_testing/"
    exit 1
fi
rsync -avF ./ "$1"
