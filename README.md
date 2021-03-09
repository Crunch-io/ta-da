# tools

A set of internal scripts and libraries, including:

* [silhouette](./silhouette) (Python): a function call stack tracer
* [elblogs](./elblogs) (Python): a collection of tools and scripts to parse and summarize ELB logs
* [elbr](./elbr) (R): an R package for doing ELB log analysis
* [superadmin](./superadmin) (R): an R package CLI for our superadmin UI
* [kaboom](./kaboom) (Python): a load-testing project using Locust
* [bootstrap](./bootstrap) (bash/Python): a set of scripts to reset your local dataset for functional (swoosh) testing.
* [pivotal](./pivotal) (typescript): A rest api endpoint that runs as an AWS lambda function accessible via
  AWS api gateway that pivotal tracker POSTs to every time a pivotal story gets updated. Also an api endpoint that returns
  a csv file containing recently accepted stories.

## Cron jobs

`elblogs`, `elbr`, and `superadmin` are used in some cron jobs that report daily and weekly on our API availability. These jobs run on our "dev" server, AKA ahsoka, as the "crunchbot" user:

    $ ssh root@ahsoka.crunch.io
    root@ahsoka:~# su - crunchbot
    crunchbot@ahsoka:~$ crontab -e

    30 * * * * $HOME/tools/elblogs/venv/bin/elb.ds /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/ /var/www/logs/AWSLogs/910774676937/by_dataset --slack >> $HOME/elbds.out 2>&1
    0 15 * * * $HOME/tools/elblogs/venv/bin/elb.summary /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/ 1 --slack >> $HOME/elbsummary.out 2>&1
    10 15 * * 1 $HOME/tools/elblogs/venv/bin/elb.summary /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/ 7 --slack >> $HOME/elbsummary.out 2>&1
    0 15 * * * $HOME/tools/elblogs/venv/bin/dog.summary 1 --slack >> $HOME/dogsummary.out 2>&1
    10 15 * * 1 $HOME/tools/elblogs/venv/bin/dog.summary 7 --slack >> $HOME/dogsummary.out 2>&1
    1 15 * * * R -e 'library(elbr); elbr:::summarize504s(1)' >> $HOME/elb504s.out 2>&1
    11 15 * * 1 R -e 'library(elbr); elbr:::summarize504s(7)' >> $HOME/elb504s.out 2>&1

The "tools" repository is checked out in crunchbot's home directory, the necessary Python packages (including elblogs) are installed in a virtualenv, and likewise the R packages are also installed for crunchbot.

See the [Slack API wrapper](./elblogs/apis/slack.py) for how messages are sent from Python (elbr also has [a similar wrapper](./elbr/R/slack.R) in R).

The crunchbot user is authorized to connect to the production server, if you need. The "superadmin" package sets up a tunnel as needed, which is destroyed on exit. 
