+++
date = "2022-02-07T21:37:48Z"
publishdate = "2022-02-07T21:37:48Z"
draft = false
title = "Subtotals and calculated differences can now be shown on graphs"
news_description = "See at a glance how your groups differ by using summary values and differences in your graphs - on screen, in dashboards and in PPTX export. Click here to learn more."
description = "See at a glance how your groups differ by using summary values and differences in your graphs - on screen, in dashboards and in PPTX export."
weight = 20
tags = ["analyses", "nets", "subtotals", "differences"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = false
no_profiles = true

+++

Subtotals have been a feature of Crunch for years, and calculated differences were added to the feature set in May 2021. They've been popular features in tables and thanks to this latest release, they're now available in graphs too. Both subtotals and differences can now be displayed in graphs in Tables & Graphs mode, as well as on dashboards and in PPTX exports, giving you the flexibility to display, save and report these summary statistics just like any other variable.

## Graphing subtotals

Take as an example the following Region variable. An editor has created three subtotals for the different regions for a marketing strategy analysis. You can see them in bold at the top of this Variable Summaries card:

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-01.png" class="img-fluid max-width-img-md">}}

Previously, a graph of this variable would just show the categories, but now you can customize the display. By default, you will see both the subtotals and the categories displayed in a graph, like this:

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-02.png" class="img-fluid max-width-img-md">}}

But by triggering the additional Display Settings panel (via the three-dots icon), you can choose whether to show just Categories, just Subtotals, or both:

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-03.png" class="img-fluid max-width-img-md">}}

This would allow you to have a simpler graph of just the region subtotals, like this:

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-04.png" class="img-fluid max-width-img-md">}}

Line graphs will allow you to choose from the categories and the subtotals via the existing "Edit" popup menu.

## Graphing calculated differences

Displaying [calculated differences](https://crunch.io/dev/features/subtotal-differences/) on graphs works slightly differently to subtotals. Take as an example this categorical variable that has had a calculated difference added:

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-05.png" class="img-fluid max-width-img-md">}}

The "Net Meets expectations" value is the result of "... exceeds my expectations" minus "... falls well short of my expectations". It can therefore be a useful single-value summary of how this brand is being perceived.

By default, only the variable's categories (and/or subtotals where applicable) will be displayed in a graph, like this:

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-06.png" class="img-fluid max-width-img-md">}}

But by clicking on the new 'delta' icon in the display controller...

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-07.png" class="img-fluid max-width-img-md">}}

 ... you can switch to viewing the calculated difference(s) instead.

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-08.png" class="img-fluid max-width-img-md">}}

This can be a particularly useful  feature when you then want to show this summary over time, like this:

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/graphing-subtotals-diffs-09.png" class="img-fluid max-width-img-md">}}

For full details of this new feature and where to find it, see the [help center](https://help.crunch.io/hc/en-us/articles/4416232124813-Graphing-Subtotals-and-Differences).

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
