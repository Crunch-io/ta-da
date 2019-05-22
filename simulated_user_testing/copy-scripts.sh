#!/bin/bash -e
# Copy useful Python scripts from this directory to another machine
if [ "$1" == "" -o "$1" == "--help" ]; then
    echo "Usage: copy-scripts <remote-hostname>"
    exit 1
fi

remote_hostname="$1"
remote_user=centos
remote_dir=/remote/simulated_user_testing

script_files="README.rst *.py"

rsync -vv $script_files "$remote_user@$remote_hostname:$remote_dir/"
