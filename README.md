# New Crunch.io Company Website

Our new website is a static site rendered by [Hugo](https://gohugo.io/).

## Local installation

If you don't have Hugo, [install it](https://gohugo.io/getting-started/quick-start/). Likewise with [yarn](https://yarnpkg.com/en/docs/install). Then,

* `yarn install` (first time only, hopefully)
* `npm run build:scss` to render the CSS
    * Alternatively, `yarn run build:scss-dev` will set up a watcher, though you'll then need a second window to...
* `hugo serve`
* Browse

If you want to preview our new site work in progress, go to https://crunch-io.github.io/crunchy/newsite/.

## Building, deploying, and git flow

The `master` branch of this repository is where the current site lives. The `src` branch is our "production" source code branch. Any changes pushed here will be built on Travis-CI and automatically published to `http://crunch.io/`.

To make changes or add new content, make a branch off of the `src` branch.

## Adding content to the current site

Posts are .md files inside the `/content` directory. There are templates and other bits that render them. See the [Hugo documentation](https://gohugo.io/documentation/) for how all that works. Generally, if you're adding a new blog post, just follow the examples of the .md files that already exist and you should be fine.
