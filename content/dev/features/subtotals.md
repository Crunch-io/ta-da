---
title: "Headings and subtotals are here"
description: "A new way to view categorical variables."
date: "2017-12-14T13:20:47-04:00"
draft: false
weight: 20
tags: ["analysis", "cubes", "subtotals"]
categories: ["feature"]
output:
  html_document:
    keep_md: true
---

At Crunch we are constantly learning new ways that our users—and their clients—think about their data, and are always excited to add new features to help improve our users' workflow. A common task in the Market Research world is to collapse two or more categories together to see how the collapsed categories compare to one another. For example, if you asked people to rate their preference on a scale of 1-10 you might want to see how the people who provide a rating between 1 and 5 compare to those who rated it between 6 and 10. This goes by a number of names like _Top Box_, _Top Two Box_, or _Nets_. Crunch has long had the ability to create a new variable by combining the categories of an existing variable, but sometimes users want to see the subtotaled values alongside the original categories instead of creating a new, separate variable.  

We recently implemented functionality that allows users to easily create and customize headings and subtotals within categorical variables. Let's take a look at what these look like in our app, as well as how to set and manipulate them using [our R `crunch` package](http://crunch.io/r/crunch/). If you want to work with headings and subtotals in R,  make sure to install our most recent version by running `devtools::install_github("Crunch-io/rcrunch", build_vignettes=TRUE)`.

# What do subtotals look like in the app?

{{< figure src="../images/subtotals-diversity.png" class="floating-right" width="250px">}}

We're going to look at data from the Stack Overflow Developer Survey that [we looked at before](../devs-as-users/). Here, we have a question which asks respondents to rate the importance of diversity on a five point scale. Perhaps the five point scale is to granular and instead we just want to get a feeling for those who _generally_ agree compared to those who _generally_ disagree. We could make a new variable that collapses "Strongly disagree" and "Disagree" responses into one category and "Somewhat agree", "Agree", and "Strongly agree" into another, but what if we wanted to see these groups right next to the other categories? Subtotals, to the rescue! Here's what that would look like in the app.

But how do we get there? First, and most importantly, we can create these subtotals in the web app be clicking on the variable's _properties_, and then clicking _Headings and Subtotals_.

{{< figure src="../images/subtotals-edit.png" class="floating-left" width="600px">}}

Once there, you're just a few clicks, drags, and drops away from fancy new subtotals. It's also possible to create subtotals and headings programmatically in R. 

# Setting subtotals in R

Let's repeat the whole process of creating subtotals from R. To begin, let's load the [crunch](http://crunch.io/r/crunch/) package and our dataset.




```r
library(crunch)
login()
ds <- loadDataset("Stack Overflow Annual Developer Survey (2017)")
```

We are again starting with an unprocessed dataset in which the diversity variable is a standard categorical variable without subtotals. We can tell this by checking with the `subtotals()` function. If it returns `NULL`, there are no subtotals.

```r
subtotals(ds$DiversityImportant)
```

```
## NULL
```

To add subtotals, we can save a list of `Subtotal` objects. Each `Subtotal` object has three things:

* `name` the label to identify the subtotal
* `categories` the categories to add subtotal (here you can use either category names or category ids)
* `after` the category that the subtotal should follow (again, either category names or category ids)


```r
subtotals(ds$DiversityImportant) <- list(
    Subtotal(name = "Generally agree",
             categories = c("Strongly agree", "Agree", "Somewhat agree"),
             after = "Strongly agree"),
    Subtotal(name = "Generally disagree",
             categories = c("Strongly disagree", "Disagree"),
             after = "Disagree")
)
```

Now, if we check `subtotals()`, we can see that we have saved them. In this output we see a few different aspects of subtotals: the `anchor` is the id of the category to put the subtotal after (matching the `after` argument in `Subtotal()`), name, aggregation function (`func`), and `args` which in the this case are the category ids to include in the subtotal.

```r
subtotals(ds$DiversityImportant)
```

```
##   anchor               name     func        args
## 1      3    Generally agree subtotal 3, 1, and 4
## 2      6 Generally disagree subtotal     5 and 6
```

And now, the subtotals are ready to be used in the app, simple as that!

# Headings
{{< figure src="../images/heading-years-coded.png" class="floating-right" width="250px">}}

Now that we have seen how to add subtotals, let's look at headings. Headings are similar to subtotals in that they are additions to categorical variables that will be displayed in the app. Although they are not particularly useful for our diversity question, for a categorical with many categories, they can help group variables visually (without adding a subtotal). Here we add some guides to different years of experience coding.

```r
subtotals(ds$YearsCodedJob) <- list(
    Heading(name = "Beginner",
            after = 0),
    Heading(name = "Novice",
            after = "Less than a year"),
    Heading(name = "Intermediate",
            after = "3 to 4 years"),
    Heading(name = "Advanced",
            after = "6 to 7 years"),
    Heading(name = "Senior",
            after = "9 to 10 years")
)

subtotals(ds$YearsCodedJob)
```

```
##   anchor         name func args
## 1      0     Beginner   NA   NA
## 2     12       Novice   NA   NA
## 3     10 Intermediate   NA   NA
## 4     16     Advanced   NA   NA
## 5      3       Senior   NA   NA
```

# Removing subtotals
Removing headings and subtotals is as simple as setting the `subtotals()` to null:

```r
subtotals(ds$YearsCodedJob) <- NULL

subtotals(ds$YearsCodedJob)
```

```
## NULL
```

# Setting many subtotals 

In the Stack Overflow survey, there are a number of questions that have the same response categories. If the category names (or ids, if we're using those) are the same, we can use the same list of `Subtotal` objects across multiple variables.

```r
agree_disagree_subtotals <- list(
    Subtotal(name = "Generally agree",
             categories = c("Strongly agree", "Agree", "Somewhat agree"),
             after = "Strongly agree"),
    Subtotal(name = "Generally disagree",
             categories = c("Strongly disagree", "Disagree"),
             after = "Disagree"))
```


```r
subtotals(ds$BuildingThings) <- agree_disagree_subtotals
subtotals(ds$LearningNewTech) <- agree_disagree_subtotals
subtotals(ds$RightWrongWay) <- agree_disagree_subtotals
```

Notice here, because each of the categories for these variables has slightly different ids, the `args` in the output differs slightly. But, because we used category names when we were constructing our list of subtotals, when we store them on the variable itself Crunch does the right thing and converts them over to the correct ids for each variable.

```r
subtotals(ds$BuildingThings)
```

```
##   anchor               name     func        args
## 1      1    Generally agree subtotal 1, 3, and 4
## 2      5 Generally disagree subtotal     6 and 5
```

```r
subtotals(ds$LearningNewTech)
```

```
##   anchor               name     func        args
## 1      3    Generally agree subtotal 3, 1, and 4
## 2      5 Generally disagree subtotal     6 and 5
```

```r
subtotals(ds$RightWrongWay)
```

```
##   anchor               name     func        args
## 1      6    Generally agree subtotal 6, 4, and 1
## 2      3 Generally disagree subtotal     5 and 3
```

# CrunchCubes and subtotals

Now that we have set subtotals on the diversity question, if we use it in a CrunchCube we can see the subtotals. Currently this is limited to the row variable in the CrunchCube, but we have plans to expand this in the future. 

```r
crtabs(~LearningNewTech + University, data = ds)
```

```
##                   University    
## LearningNewTech                No Yes, part-time Yes, full-time
##  Strongly disagree             66             13             29
##           Disagree            276             26             60
## Generally disagree            342             39             89
##     Somewhat agree           2368            162            466
##              Agree           9573            750           1927
##     Strongly agree          11347           1044           2661
##    Generally agree          23288           1956           5054
```

We can even get just the subtotals as an array from the cube if we want to ignore the constituent groups and compute specific statistics about the subtotals:

```r
subtotalArray(crtabs(~LearningNewTech + University, data = ds))
```

```
##                     University
## LearningNewTech         No Yes, part-time Yes, full-time
##   Generally disagree   342             39             89
##   Generally agree    23288           1956           5054
```

# Summary

We've already heard from enthusiastic users that headings and subtotals are helping ease their workflows, and their clients are excited to be able to see grouped subtotals right on variable cards in the app. And this is just the beginning, we are working on adding other features for transforming how variables look in the app. Have a favorite aggregation you want to see? Have an interesting use-case or workflow using headings and subtotals? [Let us know!](mailto:support@crunch.io)


