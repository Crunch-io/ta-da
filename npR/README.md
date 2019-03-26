# npR: Scripts to monitor stuff and report in Slack

## Key functions

* `elbSummary()`
* `summarize504s()`
* `slowRequestReport()`

Each of these are called from [cron jobs](https://www.notion.so/crunch/Active-cron-jobs-for-monitoring-12b8016328f2417fb2e5680257cb28d4) and report to Slack. The `with_slack_errors()` function wraps all of them in the cron jobs and reports any errors in execution to Slack as well.

The `standardizeURLs()` function can also be useful for ad-hoc log analysis where the entity IDs and query parameters are less interesting than the request endpoints.

## Installing

Clone the `tools` repository and from its top level directory,

```
R CMD INSTALL superadmin
R CMD INSTALL npR
```

If this is the first time you're installing the package, you may need to install its dependencies first, as well as those for the `superadmin` package (manually, because it's not a published package). This is most easily done within R as:

```r
# install.packages("remotes") # If you don't have that yet
remotes::install_deps("superadmin")
remotes::install_deps("npR")
```

## For developers

The repository includes a Makefile to facilitate some common tasks.

### Running tests

`$ make test`. Requires the [testthat](https://github.com/hadley/testthat) package. You can also specify a specific test file or files to run by adding a "file=" argument, like `$ make test file=elb`. `test_package` will do a regular-expression pattern match within the file names. See its documentation in the `testthat` package.

### Updating documentation

`$ make doc`. Requires the [roxygen2](https://github.com/klutometis/roxygen) package.
