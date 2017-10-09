+++
date = "2017-10-02T09:00:00-07:00"
description = "Nightwatchrun = Docker + Selenium + Nightwatch for Consistent End-to-End Testing"
draft = false
title = "Our new open-source tool eliminates the \"works on my machine\" problem for automated end-to-end browser testing. Ensure that everyone's \"machine\" has the same configuration using Docker."
weight = 20
tags = ["testing", "automation"]
categories = ["general"]

+++

At Crunch we greatly value tests. We have unit tests, functional tests, and the stack wouldn't be complete without end-to-end tests. Good tests allow us to update code quickly and confidently.

For our end-to-end testing we use [Nightwatch.js][1], a JavaScript
testing tool that uses [Selenium][2] to drive a browser to perform tests. Our goal is to be
able to test our Python backend, our REST APIs, and the
behavior of our JavaScript single-page application, using a real browser,
running real code.

Anyone that has set up Selenium knows that it can be very picky about
the versions of the different tools you should have. Selenium 3.4.0 might need
[ChromeDriver][4] 2.31 which requires [Chrome][6] 56.3920.234034249324234329 (okay, so
those version numbers may be made up), and unless you have
the exact same versions every single time, it can easily result in tests
that work on one developer's machine but not on another.

Compounding the version mismatch problem, we build and test our entire stack on a [Jenkins][8] cluster. Many of our developers would code and test on [Apple MacOS][3], but our Jenkins pipeline
was running on [Ubuntu][5] or [CentOS][7]. This led to messages like these being posted to our Slack channel:

> new variable tests pass locally so I'm sending them to jenkins for failure

and

> once again it passes locally (I’m tired of saying that). we’ll see if it
> passes the Jenkins Arbitron 5000

As a result, developers were less likely to run all tests locally before pushing because Jenkins was the final arbiter
of truth, and well, it would pass locally anyway (right?). Moreover, trying to debug this kind of "works on my machine" problem was really, really painful.

In addition to the cost to developers, operations spent an awful
lot of time testing Selenium/ChromeDriver/Chrome versions to verify that
everything continued to work. Linux package management makes installing the
latest version of a package incredibly simple, but rolling back is less so. Unless you manually keep
around the old versions of packages, you end up scouring the net for just the
right `.deb` or `.rpm` that would make everything function again. In the mean
time, developers are unhappy because you've just taken down their testing
platform.

This is where [Docker][9] containers presented a perfect solution for us.
Selenium makes Docker containers available in a variety of configurations on
the [Selenium Dockerhub][10]. Using the [standalone-chrome][11] container, we
can easily spawn a Selenium server that allows us to connect and spawn Chrome
browsers for testing. The docker container is easy to start up, easy to
tear down, and because it is self contained and doesn't require installation of
packages or software, easy to upgrade.

Hence the birth of [nightwatchrun][12], which we have just made public under the MIT license. Given our existing test suite of Nightwatch
tests, we wanted to be able to quickly spin up a new container, run our tests,
and after the tests were completed, tear down the container. This approach solved our two big problems.
Because Jenkins is running the exact same software/container as developers, "Passes locally, but not on Jenkins"
is a thing of the past. Our developers can now easily run their Nightwatch
tests against the exact same software stack used by Jenkins with [Docker for Mac][13].
Moreover, operations is no longer in the business of testing all kinds of different
  versions against each other to find the right combination of dependencies.

`nightwatchrun.sh` is a simple shell script that, given a Nightwatch.js
configuration file, will run a Docker container, get its IP address/port
number, set some environment variables, and start Nightwatch. The environment
variables are used to set the Selenium host/port number.

You can try it out yourself:

- `git clone git@github.com:Crunch-io/nightwatchrun.git`
- `yarn install`
- `./nightwatchrun.sh -c nightwatch.conf.js`

This will output something similar to:

    Riley:nightwatchrun laurenipsum$ ./nightwatchrun.sh -c nightwatch.conf.js
    Starting selenium testing against environment: stable with version latest
    Using config file: nightwatch.conf.js
    Unable to find image 'selenium/standalone-chrome:latest' locally
    latest: Pulling from selenium/standalone-chrome
    9fb6c798fa41: Pull complete
    3b61febd4aef: Pull complete
    9d99b9777eb0: Pull complete
    d010c8cf75d7: Pull complete
    7fac07fb303e: Pull complete
    64b080cf80c2: Pull complete
    4eb86df147d6: Pull complete
    4dd0b38ce61c: Pull complete
    2b0fc7beb522: Pull complete
    8682d4afe8ba: Pull complete
    8ad935df4db2: Pull complete
    e3890abf9672: Pull complete
    96df5dc43939: Pull complete
    18b664097abd: Pull complete
    984e25c49459: Pull complete
    4369356a8c66: Pull complete
    bb31d692f888: Pull complete
    c11c4dfb44fe: Pull complete
    Digest: sha256:35f9029adb074c6a23c367e0c4a5986bd7fa0fb14cdac7f8cdcc42a4613de392
    Status: Downloaded newer image for selenium/standalone-chrome:latest
    513369b2e07b93794b8ddd5837131475c58405e7ea6d60fcf8447edec7c1c227
    Today's test are run against:
    Google Chrome 61.0.3163.100 unknown
    Selenium is running at 0.0.0.0 port 32785
    Selenium is not yet alive. Sleeping 1 second.
    yarn run v1.1.0
    warning From Yarn 1.0 onwards, scripts don't require "--" for options to be forwarded. In a future version, any explicit "--" will be forwarded as-is to the scripts.
    $ "/Users/xistence/Projects/Crunch/nightwatchrun/node_modules/.bin/nightwatch" "-c" "nightwatch.conf.js"
    Running in parallel with auto workers.
    Started child process for: crunchDemo
     crunchDemo   Running in parallel with auto workers.
     crunchDemo   \n
     crunchDemo   [Crunch Demo] Test Suite
    ============================
     crunchDemo   Results for:  Demo test Crunch
     crunchDemo   ✔ Element <body> was visible after 46 milliseconds.
     crunchDemo   ✔ Testing if the page title equals "Crunch".
     crunchDemo   ✔ Testing if element <div.intro-message h3> contains text: "A modern platform".
     crunchDemo   ✔ Testing if element <div.intro-message h3 + h3> contains text: "for analytics".
     crunchDemo   OK. 4 assertions passed. (4.503s)

      >> crunchDemo finished.  


    ✨  Done in 5.04s.
    Executed tests 1 times successfully
    Removing the docker container: nightwatchrun.nightwatch.conf.js
    nightwatchrun.nightwatch.conf.js

Already have a Nightwatch.js setup? Take a look at
[nightwatch.conf.js][14], and copy over the changes necessary.

Testing with Docker has made a world of difference. Less hassle, no need to
locally install the right combination of the JRE/Selenium/ChromeDriver/Chrome,
and tests now run self-contained in a headless container, so no flash of a
browser opening or focus stealing.

If you have suggestions or improvements for nightwatchrun, please add an issue on the [Github
issue tracker][15], or provide a pull request with your suggested changes.

[1]: http://nightwatchjs.org
[2]: http://www.seleniumhq.org
[3]: https://www.apple.com/macos/
[4]: https://sites.google.com/a/chromium.org/chromedriver/
[5]: http://ubuntu.com
[6]: https://www.google.com/chrome/
[7]: https://www.centos.org
[8]: https://jenkins.io
[9]: https://www.docker.com
[10]: https://hub.docker.com/u/selenium/
[11]: https://hub.docker.com/r/selenium/standalone-chrome/
[12]: https://github.com/crunch-io/nightwatchrun/
[13]: https://www.docker.com/docker-mac
[14]: https://github.com/Crunch-io/nightwatchrun/blob/master/nightwatch.conf.js
[15]: https://github.com/Crunch-io/nightwatchrun/issues
