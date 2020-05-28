#!/bin/sh -e
export PYTHON_EGG_CACHE=$HOME/.python-eggs
export PYTHONUNBUFFERED=y

TESTING_HOME=/remote/simulated_user_testing
cd $TESTING_HOME
umask 002

# don't run if we're in maintmode (any of the different types)
if [ -f /var/lib/crunch.io/maintenance -o -f /var/lib/crunch.io/maintenance-streaming -o -f /var/lib/crunch.io/maintenance-resetdata ]; then
    exit 0;
else
    logfile=$TESTING_HOME/log/editor-bot-$(date +%Y-%m-%d-%H%M%S).log
    exec $TESTING_HOME/venv3/bin/python $TESTING_HOME/editor_bot.py simulate-editor -v "$@" > $logfile 2>&1
fi
