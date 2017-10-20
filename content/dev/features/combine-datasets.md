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

{{< figure src="../images/CombineDSSearch.png" class="floating-right">}}

Along those lines, we've recently released our Combine Datasets feature. This feature allows you to create a new dataset using a subset of variables from multiple datasets, allowing you to track these variables over time. For example, imagine a monthly political survey; every month there would be new questions, but the same question might be asked many months in a row – this feature allows you to track the responses to those common questions over all the surveys.

To use this feature, click the + in the bottom left corner while viewing a project and select **Combine Datasets**. You'll be able to search for a variable to track over multiple datasets and start the combine process.

## Selecting Objects to Combine

Combine Datasets will walk you through selecting which datasets you want to combine and selecting which variables in those datasets you want to be available in your new, combined dataset. This allows you to select multiple, possibly related, variables that are common to multiple datasets, as well as include common demographic variables.

{{< figure src="../images/CombineDSSelectVar.png" class="centered-image">}}

## Creating Time and Wave variables

{{< figure src="../images/CombineDSSelectOptions.png" class="floating-right">}}
As part of combining datasets, you can create new variables in the resulting dataset that will allow you to track your variables over time (using dataset start dates or end dates) as well as by the source dataset names, which allows you to perform analyses tracking differences over other differentiators between the datasets, such as region.

## Using the Combined Dataset

When you have finished combining datasets, you'll be able to open the new dataset, which will contain combined data for all selected variables. In addition, a dashboard will automatically have been created for you showing the combined variable you initially searched to start the combine process and, if you elected to create a time variable, the behavior of that variable over time.

{{< figure src="../images/CombineDSDashboard.png" class="centered-image">}}

## Try it out

Detailed instructions about combining datasets are available at [Combining datasets](http://support.crunch.io/crunch/crunch_combining-datasets.html). Combining datasets is a non-destructive process (the source datasets are not affected), and we encourage you to try it out if you have variables you'd like track over multiple existing datasets. If you do, please let us know what you think and if there are any other capabilities you'd like to see at support@crunch.io.
