+++
date = "2017-05-01T23:20:47-04:00"
draft = false
title = "Tab Book Improvements"
description = "By popular demand, Excel tab books just gained a bunch of new capabilities."
weight = 20
tags = ["tabbook", "export"]
categories = ["feature"]
+++

We first released the [tab book feature](http://support.crunch.io/crunch/crunch_tabbooks.html) a while back, and since then, we’ve collected a number of great suggestions for how to enrich the feature. Tab books produce a static set of tables out of many variables and put results in an Excel sheet, for offline use when you don’t need interactive features like new filters or different weights. Our recent release includes several of those enhancements, most of which are new options available to you in the “export tab book” panel.

## Export all on a single page
{{< figure src="../images/TabBookLayout.png" class="floating-right">}}

The first new option is page layout. A common request we received was to be able to export all tables in a tab book to a single sheet in the Excel workbook, rather than exporting each table to its own worksheet. While having each table in its own sheet might be more readable when you’re looking at just one, it is difficult in Excel to click through the tabs in a workbook to scan through the whole tab book. For browsing lots of results in Excel, scrolling down a single worksheet is often less tedious.

The default of one-table-per-sheet is unchanged, but to export a tab book with all tables stacked on a single Excel worksheet, toggle the “layout” setting in the export panel.

## Include a table of contents
{{< figure src="../images/TabBookToC.png" class="floating-left">}}

A table of contents can also be useful when it comes to navigating a large tab book. If you choose to add a table of contents to your tab book, the first sheet will show a list of all tables in the tab book. You can click an item to navigate directly to it — to the relevant sheet if exporting to multiple sheets or to the appropriate place in the single large table if exporting to a single page. This provides another easy way to navigate through a large tab book.

## Hypothesis testing

Hypothesis testing provides a visual heuristic, highlighting values in crosstabs that are above or below the marginal, or average in the direction of comparison (opposite of the direction of percentaging). Because it takes into account the unweighted N of respondents in each cell, it can tell you whether differences are statistically significant or not. If you have hypothesis testing enabled in the app, when you export a tab book to Excel the cell shading and p-value key will appear in the Excel spreadsheet just as it does in the app.

{{< figure src="../images/ExcelSigTest.png" class="centered-image">}}

## Unweighted counts

Previously, if you requested a tab book with a weight applied to the dataset, the “N” or “base” row of counts beneath the tables were also weighted. These are now unweighted, as they are throughout the Crunch.io app. This change allows you to see how many rows or observations in the dataset are used to compute each cell in the tables.

## Let us know what you think

If you haven’t downloaded a tab book recently, check them out. If you have suggestions for how we can improve them further, let us know!
