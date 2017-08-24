#!/bin/bash
set -ev
if [ "${TRAVIS_PULL_REQUEST}" = "false" ]; then
    git clone https://${GH_TOKEN}@github.com/$TRAVIS_REPO_SLUG.git $TRAVIS_REPO_SLUG
    cd $TRAVIS_REPO_SLUG
    git checkout -qf $TRAVIS_BRANCH
    git clone --branch v2 https://github.com/go-yaml/yaml $GOPATH/src/gopkg.in/yaml.v2
    go get -u -v github.com/spf13/hugo
    git config --global user.email "systems+crunchbot@crunch.io"
    git config --global user.name "Crunchbot"
    git clone https://github.com/crakjie/landing-page-hugo.git ./themes/landing-page-hugo

    hugo

    git clone --branch gh-pages https://${GH_TOKEN}@github.com/Crunch-io/crunchy.git ../crunchy
    rm -rf ../crunchy/newsite
    cp -r public ../crunchy/newsite
    cd ../crunchy
    git add .
    git commit -m "Updating test version of company website" || true
    git push origin gh-pages || true
fi
