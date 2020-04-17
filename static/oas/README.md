# Crunch API spec

This directory stores an openapi specification (oas) for our Crunch API.

OpenAPI Spec: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md

The purpose of the openapi standard is to provide a yaml- or json-based configuration file that describes
how your API works. That file can then be consumed by any number of 3rd party programs to render your api
documentation in HTML, create PDF documentation, use in various services that generate mock endpoints that developers can
test against even before a working api exists, etc. 

More importantly, our spec can be used by customers and other developer end-users to import into systems they
already use and love to program against the Crunch API, use in code generators, etc.

## How to view this spec
```bash
hugo server --watch=true --disableLiveReload
# this compiles the entire ta-da website and serves it on port 1313
```
Open a browser to http://localhost:1313/api/documentation.

## How to edit this spec
Create a feature branch from base branch src
```bash
git checkout src
git branch my-feature-branch
``` 
Open file `crunch-api-oas3.yaml` in [Stoplight Studio](https://stoplight.io/studio/) or your favorite text editor. Make your changes.

Test your changes by running hugo locally (see How to view this spec).

**NOTE**: If you test the spec using domain `localhost` and choose to test actual endpoints, you will run into
CORS violations. To get past this, choose the cors-buster api server.

**NOTE**: `hugo serve` will recompile and restart with every code change but the spec actually gets cached within most
browsers so you will need to peform an **empty cache and hard reload** in your browser.

**NOTE**: If you are reloading your spec frequently during testing and using the cors-buster api server, move it to the top of the list
so you don't have to choose in manually in the UI each time. However, in production we don't want the cors-buster api service to be
the first one (which the web page defaults to).

When done testing, commit your changes and git push.

Create a pull request to merge your feature branch into src branch. Somebody else (#website slack channel) will do a quick code review and perform the merge. When the merge happens, our CI process deploys the latest
changes to our production website https://crunch.io within about 15 minutes.

## Endpoint standards

When documenting Crunch endpoints, please adhere to these standards:

* Summary (endpoint name) - should be kept short in order to fit in left navigation panel

* Description - make a good description full of plain English and common sense. Stay away from jargon most novice 
users and developers are unlikely to understand. Use markdown and special elements (html tables, tab panels) to make descriptions 
look really good.

* Code samples - EVERY endpoint should include a shell/curl example in x-code-samples. Adding more languages where possible is also helpful.

* Trailing slashes in endpoint url - Crunch endpoints do not follow industry standards regarding trailing slashes. Specifically, Crunch endpoint urls require trailing slashes when most documented enterprise APIs and API best practice guides prohibit them. 
As such, many oas editors give you error messages (best case) or try to automatically strip trailing slashes (worst case). **Please ensure your final
documentation includes trailing slashes** so that endpoint testing doesn't fail.

* Request model and example: Every endpoint should contain a request model and working example. These models and envelopes **SHOULD INCLUDE the shoji envelope** so they are testable.

* Response model and example: Every endpoint should contain a response model and example. These models and envelopes **SHOULD NOT INCLUDE the shoji envelope** so they are more human-readable.

* Error responses: instead of duplicating common 401 and other error responses over and over again on every endpoint description, we will
document error responses in the overview section and only focus on success responses on each endpoint. 

* Spell-check EVERYTHING!!

# API concerns

See dedicated page [API Concerns](./API_CONCERNS.md)

# TODO
Make sure to:
1. Log out every bearer token in curl examples or else anyone will be able to use them
1. Search-replace alpha.crunch.io with app.crunch.io - as we copy/paste json after testing alpha environment so alpha is bound to appear in the final api docs
1. Other sensitive data needs to be scrubbed out - how to identify it??
1. JSON sort endpoint and schema documentation somehow
1. Remove cors-buster api servers before deploying documentation to production

