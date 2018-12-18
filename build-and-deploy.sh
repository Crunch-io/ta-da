#!/bin/bash
set -ev

publish ()
{
    if ! grep -q -e "^publishdate =" $1; then
        NOW=$(date +%Y-%m-%dT%H:%M:%OS%z)
        echo "Adding publish date for $1"
        # This adds publishdate from NOW
        perl -pe 's/(^date = ".*")/\1\npublishdate = "'"${NOW}"'"/' -i $1
        # This is how to backfill old posts by setting publishdate == date
        #perl -pe 's/(^date = ".*")/\1\npublish\1/' -i $1
    fi
}
export -f publish

install_hugo () {
    git clone --branch v2 https://github.com/go-yaml/yaml $GOPATH/src/gopkg.in/yaml.v2
    mkdir ${TRAVIS_HOME}/src
    cd ${TRAVIS_HOME}/src
    git clone https://github.com/gohugoio/hugo.git
    cd hugo
    go install

    cd ${GOPATH}/src/github.com/Crunch-io/ta-da
}

build_site () {
    npm install
    npm run build:scss
    hugo
}

if [ "${TRAVIS_PULL_REQUEST}" = "false" ]; then
    git config --global user.email "systems+crunchbot@crunch.io"
    git config --global user.name "Crunchbot"

    if [ "${TRAVIS_BRANCH}" = "src" ]; then
        # Production

        # checkout the branch so we're not on a detached head, in case we need
        # to push
        git checkout src
        # Add publishdate
        find ./content/dev -name "*.md" | xargs -n 1 -I{} bash -c "publish {}"
        git add .
        if git commit -m "Setting publication date: ${NOW}"; then
            # If there are new posts, commit and push them, then exit
            # (let the Travis build for that push be the one to deploy the site)
            git push
        else
            # Build and publish the site
            install_hugo
            build_site

            git clone -b master https://${GH_TOKEN}@github.com/$TRAVIS_REPO_SLUG.git OUTPUT
            cd OUTPUT
            git rm -rf .
            cp -r ../public/. .
            git add .
            git commit -m "Updating built site (build ${TRAVIS_BUILD_NUMBER})" || true
            git push origin master || true
        fi
    else
        # Dev (because travis.yml says only to run on src and dev)
        # Sub in the staging URL into the config so the site URLs are built correctly
        STAGING_URL=//crunch-io.github.io/crunchy/newsite/
        perl -pe 's@\Q//crunch.io/@'"${STAGING_URL}"'@' -i config.toml
        # Add publishdate, but don't commit the change to the dev branch
        find ./content/dev -name "*.md" | xargs -n 1 -I{} bash -c "publish {}"

        # Just publish to the dev site
        install_hugo
        build_site

        git clone --branch gh-pages https://${GH_TOKEN}@github.com/Crunch-io/crunchy.git ../crunchy
        rm -rf ../crunchy/newsite
        cp -r public/. ../crunchy/newsite
        cd ../crunchy
        git add .
        git commit -m "Updating test version of company website (build ${TRAVIS_BUILD_NUMBER})" || true
        git push origin gh-pages || true
    fi
fi
