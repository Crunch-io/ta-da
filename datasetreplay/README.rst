About datasetreplay
-------------------

datasetreplay picks a dataset and tries to create a copy by replaying its actions

This provides two commands:

    * ``dataset.pick`` which picks the most recently modified dataset out of the datasets list
    * ``dataset.savepoints DSID`` given a dataset returns the available savepoints.
    * ``dataset.replay DSID VERSION`` which given a dataset checks that it can replay from VERSION.

The ``test-dataset-replay.sh`` script provided uses those two commands to check all existing
datasets for replay and notifying it on slack.