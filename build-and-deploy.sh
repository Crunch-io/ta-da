#!/bin/bash
set -evx

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

build_site () {
    cd ${HOME}
    npm install --loglevel verbose
    npm run build:scss --loglevel verbose
    hugo --logLevel info
}

if [ -z "${GITHUB_PULL_REQUEST}" ]; then
    git config --global user.email "systems+crunchbot@crunch.io"
    git config --global user.name "Crunchbot"

    if [ "${GITHUB_BRANCH_NAME}" = "src" ]; then
        # Production

        # Add publishdate
        find ./content/dev -name "*.md" | xargs -n 1 -I{} bash -c "publish {}"
        git add .
        if [[ -z $(git status --porcelain) ]]; then
            # If there are new posts, commit and push them, then exit
            # (let the Travis build for that push be the one to deploy the site)
            #
            # To do this, we need to do a fresh clone with our token so that
            # we're authorized to push, and redo the find/replace there. Lame
            # but that's cheap enough
            git clone -b src https://${GH_TOKEN}@github.com/${GITHUB_REPO}.git PUBLISHDATE
            cd PUBLISHDATE
            find ./content/dev -name "*.md" | xargs -n 1 -I{} bash -c "publish {}"
            git add .
            git commit -m "Setting publication date: ${NOW}"
            git push
        else
            # Build and publish the site
            build_site

            git clone -b master https://${GH_TOKEN}@github.com/${GITHUB_REPO}.git OUTPUT
            cd OUTPUT
            git rm -rf .
            cp -r ../public/. .
            git add .
            git commit -m "Updating built site (build ${GITHUB_RUN_NUMBER})" || true
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
        build_site

        git clone --branch gh-pages https://${GH_TOKEN}@github.com/Crunch-io/crunchy.git ../crunchy
        rm -rf ../crunchy/newsite
        cp -r public/. ../crunchy/newsite
        cd ../crunchy
        git add .
        git commit -m "Updating test version of company website (build ${GITHUB_RUN_NUMBER})" || true
        git push origin gh-pages || true
    fi
fi
