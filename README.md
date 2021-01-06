# New Crunch.io Company Website

Our new website is a static site rendered by [Hugo](https://gohugo.io/).

## Local installation

If you don't have Hugo, [install it](https://gohugo.io/getting-started/quick-start/). Likewise with [yarn](https://yarnpkg.com/en/docs/install). Then,

* `yarn install` (first time only, hopefully)
* `npm run build:scss` to render the CSS
    * Alternatively, `yarn run build:scss-dev` will set up a watcher, though you'll then need a second window to...
* `hugo serve`
* Browse

## Building, deploying, and git flow

The `master` branch of this repository is where the current site lives. The `src` branch is our "production" source code branch. Any changes pushed here will be built on Travis-CI and automatically published to https://crunch.io/.

To make changes or add new content, make a branch off of the `src` branch.

To preview a published version of your branch, merge it to the `dev` branch and push. `dev` builds and is automatically published to https://crunch-io.github.io/crunchy/newsite/.

## Adding content to the current site

Posts are .md files inside the `/content` directory. There are templates and other bits that render them. See the [Hugo documentation](https://gohugo.io/documentation/) for how all that works. Generally, if you're adding a new blog post, just follow the examples of the .md files that already exist and you should be fine.

## Adding team members to the site

Team members are .yml files inside the `/data/team/members` directory. Hugo uses its data template functionality to render the page at `/layouts/team/list.html`.  To add a new team member, simply copy one of the existing .yml files and update the information contained therein to match the new employee information. Please follow the examples of existing entries for city, country. 

Please also add a professional-looking headshot image in folder `static/img/team`. The image dimensions should be 600x600 pixels.

## Release announcements

Our web app uses the [RSS feed](https://crunch.io/dev/features/index.xml) of the [features blog](https://crunch.io/dev/features/) to populate the "What's new" notification panel. Feed items are populated using the front matter following these conventions:

* Title: default is to use the same `title` as for the blog post. You may define an alternate `news_title` for use in the in-app notification, in case you want a shorter or otherwise different headline appropriate for the context of the web application.
* Description: likewise, it uses `description` unless you provide an alternative `news_description`. For blog posts, `description` is often a summary sentence or two, while for in-app announcements, you may want a "click here for more" type of call to action. `description` should be plain text only. `news_description` supports html tags.
* Date: the feed will prefer a `publishdate` and fall back to `date`. If the date listed for the item in the RSS feed is newer than the web app user's date of last reading of the notification feed, the user will be alerted that there is a new item. Date fields are a little tricky in Hugo, so the convention we follow is _fill in `date` as the time you start writing the post and do not specify `publishdate`_. When the blog is built and deployed to production, Travis will fill in the `publishdate` as the current time for any new posts--that way, `publishdate` accurately reflects when the post was deployed.

Note that emoji using the `:notation:` are valid in the title and description (but not in `date` ;).

If there is a feature announcement blog post you want to exclude from in-app announcements, include `show_news = false` in the front matter.

### Zendesk theme
A version-controlled copy of our zendesk (help center) theme is located in folder zendesk-theme. You can import this theme into Zendesk, make changes, preview the new templates, and then copy your changes back to this folder so we can maintain the current version in github.

### Targeting audiences

We want to show different announcement feeds to different users. To do this, we define audience scope limiters as boolean front matter variables. The default for all is `false`, meaning do not restrict showing the post. Currently used variables are:

* labs_only: if `true`, only show to labs users
* no_profiles: if `true`, show everywhere but profiles.crunch.io

These combine logically: if both `labs_only` and `no_profiles` are `true`, the news item will only be shown to labs users not at profiles; profiles labs users won't see the announcement.

Note that this will not affect what is shown on the feature blog: all posts will appear there. The blog website does not know who is logged into the web app or what role they may have there. These flags only govern who is shown what announcements in the app.

### Example

Given this front matter:

```toml
+++
title = "PowerPoint Deck Exports"
description = "Download your Crunch deck as a PowerPoint presentation complete with embedded graphs"
date = "2018-09-25T10:20:47-04:00"
labs_only = true
+++
```

Both the RSS feed, blog post, and blog index at `/dev/features/` will show the same title and subtitle (description) and a date of September 25, 2018.

If I want different messaging in the news feed, I can add additional fields that will override the title and description in the RSS:

```toml
+++
title = "PowerPoint Deck Exports"
news_title = "New early access feature: PowerPoint export"
description = "Download your Crunch deck as a PowerPoint presentation complete with embedded graphs"
news_description = "Decks can now be downloaded directly to PowerPoint. Click here to learn more."
date = "2018-09-25T10:20:47-04:00"
labs_only = true
+++
```

To test how how this will render on the blog _and_ display in the notifications feed, merge your branch containing this post to the `dev` branch. The blog will build and publish to https://crunch-io.github.io/crunchy/newsite/, and our alpha/testing environments will pull the RSS feed from that test version of the site. If you then log into the alpha site, you should see this post in the notifications feed--if you're a labs user (because `labs_only = true`).

When we're happy with how everything works, merge the branch to `src`. This will publish the post to our production site, and it will also fill in a `publishdate` value that is right now. It will look like this:

```toml
+++
publishdate = "2018-11-125T14:21:03-00:00"
title = "PowerPoint Deck Exports"
news_title = "New early access feature: PowerPoint export"
description = "Download your Crunch deck as a PowerPoint presentation complete with embedded graphs"
news_description = "Decks can now be downloaded directly to PowerPoint. Click here to learn more."
date = "2018-09-25T10:20:47-04:00"
labs_only = true
+++
```

That way, you don't have to worry about updating `date` before you publish to make it reflect the current time, and it will accurately match when the post was published so that the web app can tell that it's new to the user in the app.

With this deployed, labs users in production will see a notification that there's a new feature announcement.

When we decide that we want to release this feature to all, make a new branch from `src`, delete the `labs_only` **and `publishdate`** fields from the front matter, and revise the post and metadata to note that it's no longer a labs feature:

```toml
+++
title = "PowerPoint Deck Exports"
news_title = "PowerPoint export is here!"
description = "Download your Crunch deck as a PowerPoint presentation complete with embedded graphs"
news_description = "Decks can now be downloaded directly to PowerPoint. Click here to learn more."
date = "2018-09-25T10:20:47-04:00"
+++
```

You may revise `date` to be more contemporary, but it isn't strictly necessary. Do the same `dev` testing, and once again when this revision is merged to `src`, Travis will add a `publishdate` reflecting the current time, when the post is (re)published to all:

```toml
+++
publishdate = "2018-12-065T08:03:39-00:00"
title = "PowerPoint Deck Exports"
news_title = "PowerPoint export is here!"
description = "Download your Crunch deck as a PowerPoint presentation complete with embedded graphs"
news_description = "Decks can now be downloaded directly to PowerPoint. Click here to learn more."
date = "2018-09-25T10:20:47-04:00"
+++
```

## Alternative Domain Setup

GitHub pages support only one custom domain, e.g crunch.io. In order to use https://www.crunch.io, with a valid SSL certificate, a DNS redirect needs to be setup. Our DNS provider, Dnsmadeeasy, supports http redirects; however, it lacks proper support for https to https redirects. One solution is to use S3 static website hosting and cloudfront.

### Overview 

1. Create AWS managed SSL certificate 
2. Create S3 bucket with static website hosting enabled
3. Create CDN
4. Update DNS

### Step by step procedure 

1. Variable Initialization 

```toml
export REGION="eu-west-1"
export DOMAIN="www.crunch.io"
```

1. Create an AWS managed SSL certificate.

```toml
export ACM=$(aws acm request-certificate \
                            --domain-name ${DOMAIN} \
                            --validation-method DNS \
                            --subject-alternative-names ${DOMAIN#www.} \
                            --region us-east-1 \
                            --query 'CertificateArn' \
                            --output text \
                            --no-cli-pager)
```

2. Ensure the certificate validation status is SUCCESS.

```toml
aws acm describe-certificate --certificate-arn ${ACM} \
                            --region us-east-1 \
                            --no-cli-pager \
                            --query 'Certificate.DomainValidationOptions[*].[ValidationDomain,ValidationStatus]'

--- Output ---

[
    [
        "www.crunch.io",
        "SUCCESS"
    ],
    [
        "crunch.io",
        "SUCCESS"
    ]
]

```

3. (Optional) If a certificate does not pass validation, a CNAME record needs to be created. Get the record sets by running the following command. 

```toml
aws acm describe-certificate --certificate-arn ${ACM} \
                            --region us-east-1 \
                            --no-cli-pager \
                            --query 'Certificate.DomainValidationOptions[*].ResourceRecord'

--- Output ---

[
    {
        "Name": "_87b8c51f4d96e6b0eb0ab5f30c1819fa.www.crunch.io.",
        "Type": "CNAME",
        "Value": "_0a0f08d5914caefd2e01f68abd732e0e.rlltrpyzyf.acm-validations.aws."
    },
    {
        "Name": "_01598d04e21a4d0b2deef3feba09e70c.crunch.io.",
        "Type": "CNAME",
        "Value": "_33201923459074bfcc50d0428b3b7c7a.auiqqraehs.acm-validations.aws."
    }
]

```

4. Create S3 bucket. The bucket name should match the domain name. 

```toml
aws s3api create-bucket --bucket ${DOMAIN} \
                            --region ${REGION}  \
                            --create-bucket-configuration LocationConstraint=${REGION} \
                            --no-cli-pager

--- Output ---

{
    "Location": "http://www.crunch.io.s3.amazonaws.com/"
}
```

5. Create bucket configuration file to enable https redirect. 

```toml
cat <<EOF > /tmp/redirect.json
{
    "RedirectAllRequestsTo": {
        "HostName": "${DOMAIN#www.}",
        "Protocol": "https"
    }
}
EOF
```

6. Apply the bucket configuration file

```toml
aws s3api put-bucket-website --bucket ${DOMAIN} \
                            --website-configuration file:///tmp/redirect.json \
                            --no-cli-pager

```

7. Create CDN

```toml
export CDN=$(aws cloudfront create-distribution \
                            --origin-domain-name ${DOMAIN}.s3-website-${REGION}.amazonaws.com \
                            --no-cli-pager \
                            --output text \
                            --region ${REGION} \
                            --query '[ETag, Distribution.Id]')
```

9. Update CDN CNAME and Certificates using the web console. (the update file for cli would complicated so it is easier to do via the web console)

10. Update DNS eg. www.crunch.io -> cdn address.
