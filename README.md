# Crunch.io Company Website

Our website is a static site rendered by [Hugo](https://gohugo.io/).

## Local installation

If you don't have Hugo, [install it](https://gohugo.io/getting-started/quick-start/). Then,

* Clone this repo and check out this branch; `cd ta-da`
* `git clone https://github.com/crakjie/landing-page-hugo.git ./themes/landing-page-hugo`
* `hugo serve`
* `yarn run build:scss-dev` to get the css
* Browse

## Adding content

Posts are .md files inside the `/content` directory. There are templates and other bits that render them. See the [Hugo documentation](https://gohugo.io/documentation/) for how all that works. Generally, if you're adding a new blog post, just follow the examples of the .md files that already exist and you should be fine.

## Building, deploying, and git flow

The `master` branch of this repository is where the built site lives. The `src` branch is our "production" source code branch. Any changes pushed here will be built on Travis-CI and automatically published to `http://crunch.io/`.

To make changes or add new content, make a branch off of the `src` branch. If you want to preview how the published site will look, you can merge your branch to the `dev` branch and it will be built and published at https://crunch-io.github.io/crunchy/newsite/.
