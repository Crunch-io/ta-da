+++
date = "2017-10-19T23:20:47-04:00"
draft = false
title = "Combining Datasets"
description = "Combining datasets lets you track answers to questions repeated across multiple surveys over time."
weight = 20
tags = ["search", "combine datasets"]
categories = ["feature"]
+++

At Crunch, in addition to giving our users tools to process, analyze, and present new data, we are also looking for ways we can help our users to make more use out of older data. The more data you have in Crunch, the more useful it should be.

Along those lines, we've recently released our Combine Datasets feature. This feature allows you to create a new dataset using a subset of variables from multiple datasets, allowing you to track these variables over time. For example, imagine a monthly political survey; every month there would be new questions, but the same question might be asked many months in a row – this feature allows you to track the responses to those common questions over all the surveys.

{{< figure src="../images/CombineDSSearch.png" class="floating-right">}}

To use this feature, [search](http://support.crunch.io/crunch/crunch_selecting-a-dataset.html) a project for a variable you'd like to track over multiple datasets. In the search tab, slide the **Datasets / Variables** slider to **Variables** to sort the results by variable. Hover over a variable and click the **Combine Datasets** link to combine these datasets.

## Selecting Datasets

First, you'll choose which datasets to combine. By default you'll see the datasets that contain the selected variable, but you may remove any datasets you don't want or add other datasets from the project.

{{< figure src="../images/CombineDSSelectDS.png" class="centered-image">}}

## Selecting Variables

Next, you'll choose which variables you'd like to appear in the new combined dataset. You can restrict which variables are available to select to ones that appear in minimum number of datasets using the **Minimum dataset matches** option.

{{< figure src="../images/CombineDSSelectVar.png" class="centered-image">}}

## Selecting Options

Finally, you can name the new dataset and optionally create new variables based on both the survey start or end date as well as the dataset name – this allows you to perform analyses over these variables (e.g. track a variable over time or any other differentiator between the datasets, such as region).

{{< figure src="../images/CombineDSSelectOptions.png" class="centered-image">}}

See [Combining datasets](http://support.crunch.io/crunch/crunch_combining-datasets.html) in our support documentation for more detailed information about the options available when combining datasets, and please let us know if there are any other options you'd like to see at support@crunch.io.
