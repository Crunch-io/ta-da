+++
date = "2017-08-25T18:20:47-04:00"
publishdate = "2017-08-25T18:20:47-04:00"
draft = false
title = "Crunch R Package 1.18.0 Released"
description = "New tools for working with maps, derived variables, multitables, and more."
show_news = false
tags = ["R", "release", "geo"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]


+++

We've just released version 1.18.0 of the Crunch R package. Current package users should see a message when they load the package instructing you how to update to the latest version. New users (or anyone) can install this latest release from CRAN with

    install.packages("crunch")

See the [package website](/r/crunch/) for further instructions.

Since the last CRAN release in June (1.17.0), some significant features have been added. A full list of changes can be found [here](/r/crunch/news/#crunch-1-18-0), but here is an overview of the main additions.

## Mapping

Crunch-hosted geographic data can now be set and updated. Use [`geo()`](/r/crunch/reference/geo.html) on a variable to see if there is already associated geographic data. Use the [`addGeoMetadata()`](/r/crunch/reference/addGeoMetadata.html) function to match a text or categorical variable with available geodata based on the contents of the variable and metadata associated with Crunch-hosted geographic data. This function looks at the contents of the variable and the currently available geodata files that are available on Crunch. In most cases, you can set the geographic connection with just

```r
geo(ds$state) <- addGeoMetadata(ds$state)
```

Once a variable has been associated with geographic data, you can use the Crunch web app to make beautiful choropleths like this:

<div class="crunchbox-container">
    <div class="crunchbox">
        <iframe src="https://s.crunch.io/widget/index.html#/ds/b877914954c7e82db199753717ddaef9/row/00001c/column/000003?viz=geo&cp=percent&dp=0&grp=stack"></iframe>
    </div>
</div>

We're also working on a new R package for working with Crunch's geographic data, so watch this space for news about that.

## New variable builders

This release adds support for case variables, what the "[Build Categorical Variable](http://support.crunch.io/crunch/crunch_creating-a-categorical-variable.html)" interface allows you to do in the web application. [`makeCaseVariable()`](/r/crunch/reference/makeCaseVariable.html) takes a sequence of case statements to derive a new variable based on the values from other variables.

Case variables are useful when you want a categorical variable that is dependent on the contents of other variables. For example, we had two 10 point scores for how likely a respondent was to recommend ACME corp, both unaided and aided, but what we want is an overall net promoter score for ACME corp across both aided and unaided recommendations. We could create this NPS variable simply with a case variable as follows:

```r
ds_pets$ACME_NPS <- makeCaseVariable(
    Promoter = ds_pets$ACME_unaided >= 9 | ds_pets$ACME_aided >= 9,
    Neutral = ds_pets$ACME_unaided >= 7 | ds_pets$ACME_aided >= 7,
    Detractor = ds_pets$ACME_unaided <= 6 | ds_pets$ACME_aided <= 6,
    name = "ACME Net Promoter"
)
```

Case variables match the first case that evaluates to `TRUE`, so in this example, a value of `9` gets classified as "promoter" and not "neutral". If none of the cases match and there is no `else` case specified, the system default `No Data` category will be used.

`makeCaseVariable()` is incredibly powerful for making complicated derived variables that are based on anything that can be expressed with a Crunch expression. Best of all, `makeCaseVariable()` uses the power of Crunch's servers to do all of this computation, so there's no need to pull data and then send it back to Crunch. And, whenever the data in the input variables are changed or new rows are added, [your derived variable automatically updates](/r/crunch/articles/derive.html).

We also added a convenience function to create interactions of variables. [`interactVariables()`](/r/crunch/reference/interactVariables.html) takes two or more categorical variables and derives a new variable with the combination of each, like how the base R `interact()` function works, except the resulting variable is a derivation that lives on the Crunch servers, as with `makeCaseVariable()`.

## Derived variable tools

We've added some methods to help you work with derived variables more generally. First, you can check if a variable is derived with `is.derived(ds$variable)`. If it is derived, you can see its derivation expression with `derivation(ds$derived_variable)`. You can change that derivation expression by assigning a new one: `derivation(ds$derived_variable) <- ds$var1 + ds$var2`. Finally, if you want to sever the link to the variable's sources, you can "integrate" (integration is the opposite of derivation, right?) the variable by assigning a `NULL` derivation, like `derivation(ds$derived_variable) <- NULL` or you can set `is.derived(ds$derived_variable) <- FALSE`. The resulting variable will no longer update when its (former) source variables are altered.

See [derivations](/r/crunch/reference/derivations.html) for more detailed documentation and information.

## Multitables

Similar to the new tools for working with derived variables, there are also new methods for working with "[multitables](/r/crunch/reference/multitable-catalog.html)", the table header definitions composed of multiple variables that can be used interactively in the web app and to generate tab books of the dataset. Multitables can now be updated with `multitables(ds)[["Multitable name"]] <- ~ var1 + var2` formula syntax. In addition, multitables can be deleted with `multitables(ds)[["Multitable name"]] <- NULL`. Multitables also have new `name()` and `delete()` methods.

## Assorted enhancements and fixes

There are many more changes in the release; see the [full release notes](/r/crunch/news/#crunch-1-18-0) for more details. A few other new functions are worth mentioning.

* Better integration with the web application. You can copy the URL from the browser in the web app and pass it to [`loadDataset()`](/r/crunch/reference/loadDataset.html) to load the same dataset in your R session. To go the other way, call [`webApp()`](/r/crunch/reference/webApp.html) on your R dataset object and it will open it in your web browser.
* [`resetPassword()`](/r/crunch/reference/resetPassword.html) allows you to trigger a password reset from R.
* [`copyOrder()`](/r/crunch/reference/copyOrder.html) to copy the ordering of variables from one dataset to another.
* [`searchDatasets()`](/r/crunch/reference/searchDatasets.html) provides a basic interface to the Crunch search API for finding variables and datasets.
* Support for streaming data: check for received data with [`pendingStream()`](/r/crunch/reference/pendingStream.html); append that pending stream data to the dataset with [`appendStream()`](/r/crunch/reference/appendStream.html).

## New website

Finally, you may have noticed that all of the links here point to a [new website for the `crunch` package](/r/crunch/), built with the [pkgdown](https://github.com/hadley/pkgdown) static site generator. We're excited to have a new space to develop with improved, easier-to-use documentation and examples. Check back there for the latest updates to the package, and see the [Crunch + R](/r/) page for more developments.
