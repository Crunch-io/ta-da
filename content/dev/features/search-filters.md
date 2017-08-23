+++
title = "Refine your searches on Crunch"
description = "With these new search filters, you can refine your queries and find the datasets or variables you are looking for faster."
date = "2017-07-10T12:59:58-04:00"
weight = 20
draft = false
tags = ["search"]
categories = ["feature"]
+++

Search has been a part of Crunch from the beginning. In a system designed to house and share large volumes of data, the ability to quickly find the data that's important right now is critical. We're continually working to improve how data is indexed to make searching faster and more accurate, and we just added a couple new ways for you to refine your searches to get to what you are looking for faster and more easily.

## Search Filters

Two dropdown menus at the top of the panel help you to dial in your search.


{{< figure src="../images/SearchTypeFilter.png" class="floating-left">}}

On the left, the **Type filter** lets you specify **Datasets**, **Variables**, or **Categories** to limit your search to that type of object. For example, imagine you had a dataset titled "Changing attitudes towards Gender Identity"; you might try searching for it using the term **Gender**, only to find that you get dozens of results from every dataset with a "Gender" variable. By limiting the search to **Datasets**, you can quickly find what you are looking for.

<p style="clear:both;"></p>

{{< figure src="../images/SearchDateFilter.png" class="floating-right">}}

On the right, the **Date filter** lets you limit your search to recent datasets.


We use the **End Date** property of the dataset to determine the date of a dataset. This property can be viewed in [Dataset Properties](http://support.crunch.io/crunch/crunch_dataset-properties.html), and is typically set by the data owner when the dataset is imported.

## Search in a Project
{{< figure src="../images/SearchProject.png" class="floating-left">}}

Previously, if you searched from within a dataset, your search would be limited to that dataset by default, and if you searched outside a dataset, you would search all datasets. We found that for users with many datasets distributed over multiple projects, the ability to search within a project allowed them to better find what they were looking for, so we've made the default search from outside a dataset be limited to that project.

A **Search all datasets** link below the search result allows you to broaden the scope of your search, and you'll find that when searching within a dataset, the **Search project** option has been added.

In addition, the context for your search now appears at the top of the search panel (e.g. in the example, the **HipBrand** project is being searched).

We hope these search refinements will help you find what you are looking for a more efficiently. More enhancements are in the pipeline, in addition to our continual work on making the search engine faster and more intuitive. If there is any improvement to search you'd like to see, let us know at [support@crunch.io](mailto:support@crunch.io).
