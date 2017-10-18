+++
date = "2017-10-15T23:20:47-05:00"
draft = false
title = "Combine Datasets"
description = "Users can now combine datasets in order to create Trending"
weight = 20
tags = ["combine"]
categories = ["feature"]
+++

Our users often ask how they can visualize how a particular variable changes over time.
For instance, one might want to look at how the perceived direction of the country changes over time.  The
data might already be saved in "waves".  The combine datasets feature simply allows users to bring all of that data
into a single dataset.  Here's how.

## Select a variable to trend on
Click the "+" at the bottom left of the screen.  Select "combine datasets".
  
{{< figure src="../images/combine_datasets/01-plus.png" class="clear-left">}}  
  
This will prompt the search panel to pop open.  

{{< figure src="../images/combine_datasets/02-search.png" class="clear-left">}}  

Search for a variable you would like to create a trend with, and matching variables will appear with
the datasets that contain them below.  If more than one dataset matches, when you hover over the search entry 
the "combine datasets" link will appear, this is your entry point for creating a combined dataset.


## Choose which datasets you'd like to see in the trend
After selecting your trending variable, a screen will appear.
  
{{< figure src="../images/combine_datasets/03-datasets.png" class="clear-left">}}  

All of the datasets that match the variable you
selected will appear.  At this point you can select or deselect the given datasets. If you want to include
datasets that don't have a matching variable (but may match ther variables you want to trend) you can click the
link on the right to show other datasets.  If you had a project  selected when you started combining, all of 
the datasets in your projects will appear.  If you were in your personal project, personal project datasets will appear.

## Maybe there are other variables you would like to trend?
Once you've selected the datasets you want to trend, you will be able to select which variables you want to
include in your combined dataset.  


{{< figure src="../images/combine_datasets/04-variables.png" class="clear-left">}}  


Use the filter to find the variables you would like to include.  The interface
remembers which variables you have clicked even if they aren't displayed.

## Click Finish!
When you are done selecting your variables, there's a few options that you can pick before clicking combine.


{{< figure src="../images/combine_datasets/05-finish.png" class="clear-left">}}  


Depending on how many datasets and variables you have chosen, it may take some time to combine your datasets.  


{{< figure src="../images/combine_datasets/06-progress.png" class="clear-left">}}

  
When Crunch is done combining your datasets, you should see something like this:


{{< figure src="../images/combine_datasets/07-finished.png" class="clear-left">}}  


Click "View" to immediately explore your new trend dataset.


{{< figure src="../images/combine_datasets/08-dashboard.png" class="clear-left">}}  


Your new dataset will be complete with a time trend in the dashboard of the variable you chose at the beginning.
The dataset will be saved in your personal project.


## A few caveats

1) Datasets need an end date or start date defined to automatically create the dashboard with the trending variable.
   You may define the end date and start date for your datasets under properties.
2) Variables that you would like combined need to have the same alias, as this is what the system currently keys on
   for correlation.
3) There are some limitations.  You can combine up to 100 datasets.  Those datasets have to have combined less than
3000 rows in 1000 variables.  That is to say the overall size of each dataset must be 3000 rows * 1000 variables or
roughly 30mb after combined.  There is some flexibility so that if you select less datasets you can have a larger 
number variables selected.


## Future Improvements

On the roadmap for crunch is a better way of tracking variables across datasets, using tools like machine learning and
fuzzy matching in order to match datasets.  We are planning on keeping track of what matched after combining to make
combining easier and more accurate in the future!  We'd also like to eliminate the limitation on number of rows that
the target dataset can contain.