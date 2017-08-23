+++
date = "2017-07-05T11:20:47-04:00"
draft = false
title = ":bar_chart: New Header, New Font, New Graphs :chart_with_upwards_trend: "
description = "Our new visual updates make Crunch easier to use and let your data speak more clearly than ever"
weight = 20
tags = ["graphs", "design"]
categories = ["feature"]
+++

We’ve been working on updating and improving the look of Crunch, and we wanted to take moment to call out a few of the recent improvements.

## Let’s start at the top

You may have noticed that we recently updated the Crunch header.

{{< figure src="../images/VizNewHeader.png" class="centered-image">}}

This new top bar provides a more unified look throughout the application, and allows us to move user settings, dataset settings, and project settings into unobtrusive and consistently located dropdown menus. Now, you can click the dataset or project name for actions related to it, while user settings and signing out are accessed by clicking the 3 vertical dots in the upper right.

## New graphs: Better looking, better titling, better tooltips

We are very excited to be rolling out a complete refresh to all of our graphs – bar plots, histograms, time plots, dot plots – the whole nine yards. In addition to an improved visual style, these graphs more gracefully handle long variable and category names, and they include more informative tooltips, allowing you to dig into the data by hovering your cursor over the parts that interest you. Let’s take a look at a few of the new visualizations.

### Bar plots

{{< figure src="../images/VizBarPlots.png" class="floating-right">}}

Our bar plots now benefit from clearer labeling and improved interactivity. Hovering on a bar gives you the category label and the value.

In addition, you will now notice a third option available in the display controller  (in addition to table and graph), when viewing a 2-way analysis – a stacked bar plot.

### Stacked Bars

{{< figure src="../images/VizStackedBars1.png" class="floating-left">}}
When viewing a 2-way analysis, the display controller now offers two options for graphs – a grouped bar chart (seen above), as well as stacked bars. Stacked bars offer another way to see the data and make comparisons, and they offer greater information density, allowing you to make comparisons across more groups.

<p style="clear:both"></p>

{{< figure src="../images/VizStackedBars2.png" class="floating-right">}}
You can toggle the base used for the stacked bars (i.e. whether the second variable is shown relative to the first variable or relative to the base as a whole), using the percentage-direction control.

### Time plots
{{< figure src="../images/VizTimePlots.png" class="floating-left">}}
While time plots are not new to Crunch, we’ve made some major improvements. In addition to increased legibility, you can now click categories in the axis to hide them from the graph, or double-click one to show only that category. Hovering on the graph lets you see the value at any point along the line, allowing you to see broad trends or to zero in on individual values.

## Proxima Nova: New look, new typeface
Eagle-eyed Crunch users may have noticed that our type face has changed. After much consideration, we’ve decided to switch from Avenir to Proxima Nova. We find Proxima Nova to be more legible through a wider range of sizes, giving us more options in our design of tables, graphs, and the interface as a whole.

## More to come
We have more improvements and additions to our visualizations planned for the coming months. We’d love to hear what you think about these updates, as well as anything you’d like to see us add over at [support@crunch.io](mailto:support@crunch.io).
