+++
date = "2021-07-06T11:27:47-04:00"
publishdate = "2021-07-06T11:27:47-04:00"
draft = false
title = "Sort your graph categories automatically"
news_description = "Sort the categories of your graphs automatically based on value, and have the order update dynamically as you apply filters. Click here to learn more."
description = "Sort the categories of your graphs automatically based on value, and have the order update dynamically as you apply filters."
weight = 20
tags = ["analyses", "graphs", "dashboards"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = false
no_profiles = true

+++

You’ve been able to sort categories in *tables* in Crunch for a long time, but previously when you switched to a graph, that sorting was lost and the graph would show the categories in their original variable order. Now, the sorting you apply in a table will be carried through into a graph when you switch visualization type, as well as being made part of the analysis definition when you save a graph to the deck. That means that the sorted order will show in dashboards, including when you apply a filter, and in PowerPoint exports.

Sorting a table works as it always has - by clicking on the column header (once for descending, again for ascending and again to return to original variable order). Crunch will show a small chevron to indicate sort direction. Once you've sorted your table, simply switch to another visualization type to see that sort order reflected in the categories. The analysis will remain sorted in this way, even if you apply filters (i.e. the categories will change order, as applicable, to retain the largest-to-smallest sequence).

{{<figure src="https://crunch.io/dev/features/images/sort-by-value_01.jpg" class="img-fluid">}}

Single-dimension analyses (i.e. those that show just one variable) can also be sorted *after* they've been saved to the deck. In the edit panel for a saved analysis there will be a "Categories" tab and we've added a new toggle option here for switching between Manual, Descending and Ascending.

{{<figure src="https://crunch.io/dev/features/images/sort-by-value_02.jpg" class="img-fluid">}}

Dragging-and-dropping any category into a new position will automatically revert an analysis to being manually sorted.

The known limitation of this first version is that we’re not offering the ability to ‘anchor’ a category to a position – most commonly used to keep “Other” or “None” etc. categories at the bottom. For now, the only way to achieve this is the previous method of manual dragging-and-dropping. We intend to offer category anchoring in the future.

For full details of this new feature and where to find it, see the [help center](https://help.crunch.io/hc/en-us/articles/360039306152-Tables-and-charts-with-drag-and-drop#sort-tables-graphs).

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
