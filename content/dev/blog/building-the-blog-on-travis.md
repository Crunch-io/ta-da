+++
categories = ["general"]
date = "2017-05-18T21:12:10-07:00"
description = "Life is short. Here are seven tips to help you automate your static-site building so that you can focus on more important things."
draft = false
tags = ["automation"]
title = "Using Travis-CI to Build Static Sites"
weight = 20
images = ["https://crunch.io/img/og-image.png"]

+++

At Crunch.io, we're fervent believers in automation. If something requires a human to remember to do an extra manual step, it won't happen consistently. We automate test running so that we don't have to fix the same bug twice. We write code to do tedious tasks so that we can devote our mental energy to harder problems. We automate processes and policies so that developers don't have remember the right things to do—the build and continuous-integration systems guide us.

Occasionally we find an area where we are doing manual, menial tasks, and someone will carve out some time to automate them away. Recently we noticed that our [API documentation](http://docs.crunch.io) wasn't consistently being updated. It wasn't that developers were failing to write documentation updates with each change—that part is integrated with our build and review process. Rather, the updates were to markdown files, but the [static site generator](https://github.com/lord/slate) that turned them into HTML wasn't being run regularly.

GitHub builds Jekyll sites automatically, and we use it for some other pages. But this one, while in Ruby, required an extra build step. And we don't use Ruby in production and don't have any Ruby developers on the team, so there was a nontrivial setup cost associated with being able to build the docs website. Some of us (on OSX/macOS) struggled to get a working Ruby setup. So no one really wanted to mess with it.

Plus, someone had to remember to take action when there were changes to the documentation markdown. Even the best multitaskers among us struggled to keep track consistently. As a result, the published documentation was often only updated when someone asked us about an API that we knew was documented but didn't show up on docs.crunch.io.

That situation was not improving on its own, and as we were starting to add another static site (this blog), also using GitHub Pages and also not using Jekyll—it uses Hugo—we figured it was time to learn how to automate away this build step.

# Automating the site build

Our goal: automatically build the site and deploy on GitHub Pages using Travis-CI. On each push to the `master` branch, build it, commit the built code to the `gh-pages` branch, and push that. GitHub Pages then updates what it is serving.

There [are](https://blog.christophvoigt.com/setting-up-hugo-with-github-pages/) [lots](http://speps.github.io/articles/hugo-setup/) [of](http://rcoedo.com/post/hugo-static-site-generator/) [blog](https://pghalliday.com/github/ssh/travis-ci/2014/09/19/auto-build-and-deploy-github-pages-with-travis-ci.html) [posts](https://www.metachris.com/2017/04/continuous-deployment-hugo---travis-ci--github-pages/) about how to use Travis to build your static site. Many of them were helpful. Some gave bad advice. None were complete enough to just drop in and use. In the end, it took nine attempts to get the build-and-publish working for the API docs and ten attempts for the dev blog. The following discussion synthesizes the useful parts of those posts and adds (or emphasizes differently) the parts that we found essential. The discussion does assume familiarity with GitHub, Travis-CI, and static-site generators, so if you need more context on those, start with those other blog posts (or Google).

## 1. Make a GitHub API key and encrypt it

Your build script needs more access to the repository on GitHub than Travis typically does—it needs to be able to push. To allow this, generate an API key for this job, encrypt it, and add it to the .travis.yml.

First, go to the GitHub site and [generate a new token](https://github.com/settings/tokens). You only need to give it access to the `public_repo` scope because your GitHub Pages repository needs to be public anyway.

Once you have that, encrypt it using travis's Ruby library (yes, you still need a functioning Ruby environment, but only this once). See their [instructions](https://docs.travis-ci.com/user/encryption-keys/). Note that you're not just encrypting the API token, you're encrypting the pair of `NAME=tokenstring`, so remember that variable name for use in your script. To keep with the examples here (and borrowing from somewhere else on the internet), we did:

    gem install travis
    travis encrypt GH_TOKEN=token --add

where `token` is the string copied from the GitHub page when the token was generated. Do this in the directory of your git repository, and the `--add` it will add it to the .travis.yml file for you.

## 2. Create an orphan gh-pages branch

In order to set "gh-pages" as the branch from which to [serve the website](https://help.github.com/articles/configuring-a-publishing-source-for-github-pages/), the branch needs to exist. And you don't want or need it to have any of your markdown and theme code—you just want it to have the generated site. So, create an empty "orphan" branch called "gh-pages" and push that. [This post](http://www.bitflop.dk/tutorials/how-to-create-a-new-and-empty-branch-in-git.html) has a simple explanation; [here](https://gist.github.com/seanbuscay/5877413) is some sample code that's four lines too long.

Once you've pushed, you can turn on GitHub Pages. Now you're ready to start composing the .travis.yml file that will drive the build.

## 3. Re-clone the repository

Travis will as a matter of course clone your github repository and checkout the current branch. Unfortunately, for efficiency, it only clones the active commit—there's no branch history, and importantly, no other branches. You need to be able to build on master, then checkout gh-pages and commit the build artifacts there. In order to do this, clone the repository again and get the full tree. So this goes in one of the sections that runs code:

    - git clone https://${GH_TOKEN}@github.com/$TRAVIS_REPO_SLUG.git $TRAVIS_REPO_SLUG

## 4. Run only on the master branch

We don't want any development branches to be built and pushed to our production site automatically. And moreover, if the Travis workflow is build, commit, and push to gh-pages, each build would kick off another build if we didn't restrict it. So this goes in the .travis.yml:

    branches:
      only:
      - master

## 5. Add some git config

The commit will fail if it doesn't have a username. You could inline it with the commit, but it reads more cleanly if you set them up before.

    - git config user.email "you@example.com"
    - git config user.name "You"

## 6. On commit, pass if there are no changes

If there are no changes, `git commit` will exit with an error code, which will terminate your script and mark your build as failed. Normally, there will be changes to commit, but sometimes, like when you're tweaking your .travis.yml to get the build to work, there won't be. However, if you add `|| true` to the end of the line, the script will continue to evaluate. So we added that to the `git commit` and `git push` lines.

## 7. Push quietly

A few blog posts recommended adding the `--quiet` flag to the `git push` command, and/or to redirect the standard output to `/dev/null`, because otherwise it would print your GitHub token, thus defeating the purpose of encrypting it in step 1. Eventually someone realized that this was a [security vulnerability](https://blog.travis-ci.com/2017-05-08-security-advisory) by which tokens could be harvested from Travis logs. Consequently, Travis has presumably fixed this so that `push` doesn't print your token anymore, so it's likely fine to omit this detail now, but we've [left](https://github.com/Crunch-io/clatter/blob/master/.travis.yml#L31) the `> /dev/null 2>&1` in there anyway—it's not hurting anything, and we weren't looking at the push log anyway once we got the flow working.

# Walking through the build scripts

Here are the end results. For the [API docs](https://github.com/Crunch-io/apidocs/blob/master/.travis.yml), we use a Ruby container, install the `bundler` package, do a fresh clone of the repository so we get all the branches, and then install necessary dependencies. In the [build script](https://github.com/Crunch-io/apidocs/blob/master/build.sh) called next, the HTML and other static files are generated. Then we checkout the `gh-pages` branch, delete the old static files, and copy in the ones we just built. After that, commit, push, and the site is updated.

For the [dev blog](https://github.com/Crunch-io/clatter/blob/master/.travis.yml), the flow is a little different: we use Hugo (golang) instead of a Ruby library, and instead of pushing to `gh-pages`, we [copy the built blog to serve as a subdirectory](https://github.com/Crunch-io/clatter/blob/master/.travis.yml#L19-L21) of our company website, which is hosted in a _different_ repository. (We do also publish a version to `gh-pages`, a holdover from our initial testing process, so that's woven in the script too, but it's not a necessary part.)

There are a few Hugo-specific features in the dev blog build as well. First, the "theme" is not part of our repository, so we need to install it by cloning it from GitHub as well. (Note that this means that you should be sure to add the "themes" directory to your `.gitignore` file, as well as the "public" directory to which the built site gets generated.) Second, as [this blog](http://rcoedo.com/post/hugo-static-site-generator/) notes at the very bottom, by some ~~quirk~~ feature of how Travis builds go projects, the Hugo build will fail unless you provide a Makefile, _which can be empty_. So, `touch Makefile` and commit before you throw the job up on Travis.

# Final observations

## Script or YAML?

Some blogs proposed putting your build script into a .sh file that the .travis.yml file invokes. We didn't find that to help anything. Unless you're planning to run your build script outside of Travis too, there doesn't seem to be a reason to put your build steps outside of the YAML file itself. In fact, it just complicated things—one more file to look at to debug, not to mention that you had to deal with making the shell script executable. Either way works—one of our repos uses a script, the other is all in YAML—but all in the .travis.yml seemed simpler. It evaluates like a script.

## before_script, install, after_success, ...

Travis's YAML file supports various blocks that get evaluated sequentially. Where should the code go?

It doesn't really matter. Travis-CI is designed for running automated tests. In that context, it makes sense that you have different contexts for setup, running the tests, and things that you'd only do if the tests passed, and so on. Here, we're just running a script. Organize your script in a way that makes sense to you, but you could put everything in `install`, or `script`, or whatever, and it should run just the same.

## Just automate it.

Even if it takes you nine tries to get the Travis build set up correctly, that's time well spent. Automation isn't just about [saving](https://xkcd.com/1319/) [time](https://xkcd.com/1205/): it's about [saving mental energy](https://www.johndcook.com/blog/2015/12/22/automate-to-save-mental-energy-not-time/), and about making sure that important things happen without having to remember to do them. After setting up these jobs on Travis, we can much more easily push updates to our static sites and don't have to remember to do an extra build step. That frees us to build more cool stuff!
