---
title: "Subtotals for Categorical Data"
description: "Enhance your analyses by adding subtotals to your tables. See summary statistics of interest at a glance."
date: "2018-01-14T13:20:47-04:00"
draft: false
weight: 20
tags: ["analysis", "nets", "subtotals"]
categories: ["feature"]
---

{{< figure src="../images/subtotals-diversity.png" class="floating-right" width="250px">}}

At Crunch, we are constantly searching for ways to help our customers---and their clients---gain insights from their data. A common task in the market-research world is to take data that is essentially a scale---rate from 1 to 10, or an ordinal range of responses from "Strongly agree" to "Strongly disagree"---and collapse it into a smaller number of bins. For example, if you asked people to rate their preference on a scale of 1-10 you might want to see how the people who provide a rating between 1 and 5 compare to those who rated it between 6 and 10. This goes by a number of names like _Top Box_, _Top Two Box_, or _Nets_.

Crunch has long had the ability to create a new variable by [combining the categories](http://support.crunch.io/crunch/crunch_creating-a-combined-variable.html) of an existing variable. Sometimes, though, you want to see the subtotals alongside the original categories.  

Our new "headings and subtotals" feature allows you to do just that. The example above shows how subtotals look in the web app, using an example variable card from the Stack Overflow Developer Survey that we have [used previously](../devs-as-users/). Here, we have a question which asks respondents to rate the importance of diversity on a five point scale.

Perhaps for our purposes, we think the five point scale is too granular, and instead we just want to get a feeling for those who _generally_ agree compared to those who _generally_ disagree. That grouping may make it easier for us to report conclusions from the data, or make it easier for others to interpret. We could make a new variable that collapses "Strongly disagree" and "Disagree" responses into one category and "Somewhat agree", "Agree", and "Strongly agree" into another. But what if we want it both ways: we want to see the higher level, aggregated values _and_ the breakdown of percentages within each group? Maybe there are within-group differences of interest---say, most of those who agree agree strongly, while those who disagree only do so "somewhat"---that we don't want to obscure completely.

Subtotals can help. To make them appear in Crunch, we add some properties to the variable so that every time it is loaded, whether in the card view, the crosstabbing view, or any reports, the subtotals are shown. To define the subtotals for a variable in the web app, click on the variable's _properties_, and then select _Headings and Subtotals_. Once there, you're just a few clicks, drags, and drops away from fancy new subtotals.

{{< figure src="../images/subtotals-edit.png" class="centered-image" width="600px">}}

If you want to script, it's also possible to create subtotals and headings [programmatically in R](http://crunch.io/r/crunch/articles/subtotals.html).

We've already heard from some enthusiastic users that headings and subtotals are helping ease their workflows, and their clients are excited to see grouped subtotals right on variable cards in the app. Have a favorite aggregation you want to see added to Crunch? Have an interesting use-case or workflow using headings and subtotals? [Let us know!](mailto:support@crunch.io)
