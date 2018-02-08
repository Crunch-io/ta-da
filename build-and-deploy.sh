#!/bin/bash
set -ev
if [ "${TRAVIS_PULL_REQUEST}" = "false" ]; then
    git clone --branch v2 https://github.com/go-yaml/yaml $GOPATH/src/gopkg.in/yaml.v2
    go get github.com/magefile/mage
    go get -d github.com/gohugoio/hugo
    cd $GOPATH/src/github.com/gohugoio/hugo
    mage vendor
    mage install
    cd $GOPATH/src/github.com/Crunch-io/ta-da
    git config --global user.email "systems+crunchbot@crunch.io"
    git config --global user.name "Crunchbot"

    if [ "${TRAVIS_BRANCH}" = "src" ]; then
        # Production
        git clone https://github.com/crakjie/landing-page-hugo.git ./themes/landing-page-hugo
        hugo

        git clone -b master https://${GH_TOKEN}@github.com/$TRAVIS_REPO_SLUG.git OUTPUT
        cd OUTPUT
        git rm -rf .
        cp -r ../public/. .
        git add .
        git commit -m "Updating built site (build ${TRAVIS_BUILD_NUMBER})" || true
        git push origin master || true
    else
        # Dev
        # Sub in the staging URL into the config so the site URLs are built correctly
        STAGING_URL=https://crunch-io.github.io/crunchy/newsite/
        sed -i 's@http://crunch.io/@'"$STAGING_URL"'@g' config.toml
        npm install
        npm build:scss
        hugo

        git clone --branch gh-pages https://${GH_TOKEN}@github.com/Crunch-io/crunchy.git ../crunchy
        rm -rf ../crunchy/newsite
        cp -r public/. ../crunchy/newsite
        cd ../crunchy
        git add .
        git commit -m "Updating test version of company website (build ${TRAVIS_BUILD_NUMBER})" || true
        git push origin gh-pages || true
    fi
fi