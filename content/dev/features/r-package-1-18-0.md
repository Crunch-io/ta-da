+++
date = "2017-08-22T23:20:47-04:00"
draft = false
title = "Crunch R Package 1.18.0 Released"
description = "asdf"
weight = 20
tags = ["R", "release", "geo"]
categories = ["feature"]
+++

We've just released version 1.18.0 of the Crunch R package. Current package users should see a message when they load the package instructing you how to update to the latest version. New users (or anyone) can install this latest release from CRAN with

    install.packages("crunch")

See [README.md](https://github.com/Crunch-io/rcrunch/blob/master/README.md) for further instructions.

Since the last CRAN release in June (1.17.0), some significant features have been added. A full list of changes can be found in (link), but here is an overview of the main additions.

## Mapping

* Crunch-hosted geographic data can now be set and updated. Use `geo()` on a variable to see if there is already associated geographic data.
* Use the `addGeoMetadata()` function to match a text or categorical variable with available geodata based on the contents of the variable and metadata associated with Crunch-hosted geographic data.

This function looks at the contents of the variable and the currently available geodata files that are available on Crunch. If there is a single match, you can set the geographic connection with `geo(ds$state) <- addGeoMetadata(ds$state)`. If there isn't a single match, you will be given a set of geodata files that could match, and you can match them as follows (this information will be provided to you ):
```{r}
geo(ds$country) <- addGeoMetadata(ds$country)

# There is more than one possible match. Please specify the geography manually:
#        value      geodatum_name                                geodatum   property
#7  0.09615385          Countries http://app.crunch.io/api/geodata/00001/    country
#9  0.09615385 Countries Topojson http://app.crunch.io/api/geodata/00002/    country

geo(ds$country) <- CrunchGeography(
    geodatum = http://app.crunch.io/api/geodata/00001/,
    feature_key = "name",
    match_field = "country"
)
```

Once a variable has been associated with geographic data, you can use the Crunch webapp to make [beautiful choropleths](https://s.crunch.io/widget/index.html#/ds/b877914954c7e82db199753717ddaef9/row/00001c/column/000003?viz=geo&cp=percent&dp=0&grp=stack) with drag and drop ease. We're also working on a new R package for working with Crunch's geographic data, so watch this space for news about that.

See `?geo` for more detailed documentation and information.

## New variable builders

* Added support for case variables (#36): `makeCaseVariable()` takes a sequence of case statements to derive a new variable based on the values from other variables.

Case variables are useful when you want a categorical variable that is dependent on the contents of other variables. For example, we had two 10 point scores for how likely a respondent was to recommend ACME corp, both unaided and aided, but what we want is an overall net promoter score for ACME corp across both aided and unaided recommendations. We could create this NPS variable simply with a case variable as follows:
```{r}
ds_pets$ACME_NPS <- makeCaseVariable(
    promoter = ds_pets$ACME_unaided >= 9 | ds_pets$ACME_aided >= 9,
    neutral = { ds_pets$ACME_unaided >= 7 & ds_pets$ACME_unaided <= 8 } |
              { ds_pets$ACME_aided >= 7 & ds_pets$ACME_aided <= 8 },
              detractor = ds_pets$ACME_unaided <= 6 | ds_pets$ACME_aided <= 6,
              name = "ACME_NPS"
)
```
 Case variables match the first case that evaluates to `TRUE`. If none of the cases match and there is no else case specified, the system default `No Data` category will be used.

 `makeCaseVariable()` is incredibly powerful for making complicated derived variables that are based on anything that can be expressed with a Crunch expression. Best of all, `makeCaseVariable()` uses the power of Crunch's servers to do all of this computation, there's no need to pull data and then send it back to Crunch. See `?makeCaseVariable` for more detailed documentation and information.

* Added a function to create interactions of variables (#42): `interactVariables()` takes two or more categorical variables and derives a new variable with the combination of each. See `?interactVariables` for more detailed documentation and information.

## Derived variable tools

* See the formula that defines derived variables with `derivation(ds$derived_variable)`. Additionally, you can change the derivation by assigning a Crunch expression to the derivation: `derivation(ds$derived_variable) <- ds$var1 + ds$var2`
* Check if a variable is derived with `is.derived(ds$variable)`
* Integrate (or realize or instantiate) a derived variable with `derivation(ds$derived_variable) <- NULL` or `is.derived(ds$derived_variable) <- FALSE`. This is useful to separate the connection between the derived variable and the source variables in the derivation expression.

See `?derivations` for more detailed documentation and information.

## Multitables

Similar to the new tools for working with derived variables, there are also new methods for working with "multitables", the table header definitions composed of multiple variables that can be used interactively in the web app and to generate tab books of the dataset.

* Multitables can now be updated with `multitables(ds)[["Multitable name"]] <- ~ var1 + var2` syntax. Similarly, multitables can be deleted with `multitables(ds)[["Multitable name"]] <- NULL`. Multitables also have new `name()` and `delete()` methods.

See `?multitables` for more detailed documentation and information.


## Assorted enhancements and fixes

There are many more changes in the release; see the full release notes for more details. A few other new functions are worth mentioning.

* Better integration with the web application. You can copy the URL from the browser in the web app and pass it to `loadDataset()` to load the same dataset in your R session. To go the other way, call `webApp()` on your R dataset object and it will open it in your web browser.
* `resetPassword()` allows you to trigger a password reset from R.
* `copyOrder()` to copy the ordering of variables from one dataset to another.
* `searchDatasets()` provides a basic interface to the Crunch search API for finding variables and datasets.
* Support for streaming data: check for received data with `pendingStream()`; append that pending stream data to the dataset with `appendStream()`.

More exciting changes are coming!
