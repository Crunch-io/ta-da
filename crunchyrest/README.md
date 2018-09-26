# crunchyrest

The goal of crunchyrest is to allow you to set up a REST API for Crunch services by hacking into a Shiny app. Of course, this isn't a good way to set up a JSON API server: you shouldn't use Shiny for that. But, if you can't easily set up "proper" web services that access R's capabilities, but you can deploy Crunchy apps, this will work :)

## Installation

You can install the development version of `crunchyrest` from [GitHub](https://github.com/) with:

``` r
# install.packages("devtools")
devtools::install_github("Crunch-io/tools/crunchyrest")
```

As this is a private repository, installation by `install_github()` requires a GitHub personal access token, so on jupyter.crunch.io, you'll need to provide one. See `?devtools::install_github`. It may be easier and more secure to just tar up a local copy, upload to Jupyter, untar and install.

## Example

See `app.R` for a minimal example that returns request parameters as JSON. This requires that the request be authenticated with Crunch, but it does not actually touch the Crunch API. To do so, you can write code that uses the `crunch` package as if you were logged in in a local R session--all `crunch` functions are available.

## Caveats and limitations

Surely there are many. As we discover them, we'll enumerate here.