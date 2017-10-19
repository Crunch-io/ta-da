+++
date = "2017-10-15T23:20:47-05:00"
draft = false
title = "Combine Datasets"
description = "Users can now combine datasets in order to create Trending"
weight = 20
tags = ["combine"]
categories = ["feature"]
+++

At Crunch, in addition to giving our users tools to process, analyze, and present new data, we are also looking for ways we can help our users to make more use out of older data. The more data you have in Crunch, the more useful it should be.

For example, you might want to look at how the perceived direction of the country changes over time using surveys that were taken in multiple waves. The combine datasets feature allows you to bring that data into a single dataset where you can track it over time.  Here's how.

## Select a variable to trend on
Click the "+" at the bottom left of the screen.  Select "combine datasets".

{{< figure src="../images/CombineDSplus.png" class="clear-left">}}  

This will open the search panel.  

{{< figure src="../images/CombineDSsearch.png" class="centered-image">}}  

Search for a variable. The search results will show the matching variable names; you can click the arrow on the left to see all datasets that contain a given variable. Hover over the search entry to reveal the **Combine Datasets** link. Click it to start the process of combining datasets.

## Choose which datasets you'd like to see in the trend
After selecting the trending variable, the dataset selection screen will appear.

{{< figure src="../images/CombineDSdatasets.png" class="centered-image">}}  

All datasets that match the variable you selected will be displayed and can be selected or deselected. If you want to include
datasets don't have the the searched variable (but may match other variables you want to include), click **Show all datasets in project** to show other datasets in the current project.  

## Select other variables you would like to trend
Once you've selected the datasets you want to combine, click **Next** to open the variable selection screen, where you can select which variables you want to
include in the combined dataset.  

{{< figure src="../images/CombineDSvariables.png" class="centered-image">}}  

Browse or use the filter to find the variables you would like to include.  You can restrict which variables are displayed to ones that appear in minimum number of datasets using the **Minimum dataset matches** option. Click **Next** to continue.

## Select options
Finally, you can name the new dataset and optionally create new variables based on both the survey start or end date as well as the dataset name – this allows you to perform analyses over these variables (e.g. track a variable over time or any other differentiator between the datasets, such as region).

{{< figure src="../images/CombineDSfinish.png" class="centered-image">}}  

Depending on how many datasets and variables you have chosen, it may take some time to combine your datasets.  

When Crunch is done combining your datasets, click **View** to explore your new dataset.

{{< figure src="../images/CombineDSdashboard.png" class="clear-left">}}  

If you created a new time variable, the dashboard will automatically include a time series of the variable you chose in your initial search.

## More details

See [Combining datasets](http://support.crunch.io/crunch/crunch_combining-datasets.html) in our support documentation for more detailed information about the options available when combining datasets.

Our future plans for this feature include better way of tracking variables across datasets, using tools like machine learning and
fuzzy matching in order to match datasets.  We are planning on keeping track of what matched after combining to make
combining easier and more accurate in the future. If there are any other capabilities you'd like to see at support@crunch.io.
