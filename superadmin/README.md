# superadmin: CLI for Crunch Superadmin

## Key functions

* `getDatasets(dsid, name, email)`
* `getUser(id, query)`, where `query` is anything you'd enter in the superadmin page, like "preferences.labs:true"
* `getUsers(query)`
* `featureFlags()` lets you view and set the user's "preferences" feature flags
* `getSlowRequests()`

All functions manage the connection to the superadmin via SSH tunnel; the tunnel is destroyed when the R process exits. If you want to connect to a non-production host such as alpha, call `superConnect("alpha")` directly before making any other queries.

There is also an exported `crunchbot()` function that JSON-serializes the output of whatever is returned. This makes it easy to call R as a subprocess and bring in the results from stdout.

## Installing

Clone the `tools` repository and from its top level directory,

```
R CMD INSTALL superadmin
```

If this is the first time you're installing the package, you may need to install its dependencies first. This is most easily done within R as:

```r
# install.packages("remotes") # If you don't have that yet
remotes::install_deps("superadmin")
```

## For developers

The repository includes a Makefile to facilitate some common tasks.

### Running tests

`$ make test`. Requires the [testthat](https://github.com/hadley/testthat) package. You can also specify a specific test file or files to run by adding a "file=" argument, like `$ make test file=datasets`. `test_package` will do a regular-expression pattern match within the file names. See its documentation in the `testthat` package.

### Updating documentation

`$ make doc`. Requires the [roxygen2](https://github.com/klutometis/roxygen) package.
