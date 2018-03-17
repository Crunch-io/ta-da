# elbr: Tools for Analyzing AWS ELB Logs

[![Build Status](https://travis-ci.org/nealrichardson/elbr.png?branch=master)](https://travis-ci.org/nealrichardson/elbr)  [![codecov](https://codecov.io/gh/nealrichardson/elbr/branch/master/graph/badge.svg)](https://codecov.io/gh/nealrichardson/elbr)
[![cran](https://www.r-pkg.org/badges/version-last-release/elbr)](https://cran.r-project.org/package=elbr)

## Installing

<!-- `elbr` can be installed from CRAN with

    install.packages("elbr") -->

The pre-release version of the package can be pulled from GitHub using the [devtools](https://github.com/r-lib/devtools) package:

    # install.packages("devtools")
    devtools::install_github("nealrichardson/elbr")

## For developers

The repository includes a Makefile to facilitate some common tasks.

### Running tests

`$ make test`. Requires the [testthat](http://testthat.r-lib.org) package. You can also specify a specific test file or files to run by adding a "file=" argument, like `$ make test file=read`. `testthat::test_package()` will do a regular-expression pattern match within the file names.

### Updating documentation

`$ make doc`. Requires the [roxygen2](https://github.com/klutometis/roxygen) package.
