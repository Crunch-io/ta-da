+++
date = "2020-02-25T09:18:29-04:00"
publishdate = "2020-02-25T15:19:37+0000"
draft = false
title = "Show value labels on graphs"
news_description = "Users can now decide whether to show value labels for graphs and charts, both in Tables & Graphs mode and on dashboards. Click here to learn more."
description = "Users can now decide whether to show value labels for graphs and charts, both in Tables & Graphs mode and on dashboards."
weight = 20
tags = ["analyses", "graphs"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = false
no_profiles = true

+++

Users can now decide whether to show value labels for graphs and charts, both in Tables & Graphs mode and on dashboards. Value labels are these small numbers on graphs that show you the value represented by that bar/column/segment...

{{< figure src="dev/features/images/value-labels-on-chart.png" class="img-fluid">}}

With the new feature turned on, these value labels will be displayed on all graphs you create. With the feature turned off (the default), the user needs to hover over a chart element to see a tool-tip with this value.

If you're happy with the tool-tip approach, you don't need to do anything. But if you'd like to have these values always displayed, you can turn this feature on via the three-dots menu in the play-controller at the bottom of your screen, choosing the option "Show value labels"...

{{< figure src="dev/features/images/value-labels-dropdown.png" class="img-fluid">}}

Analyses saved to the deck will have this property saved with them, and this will then be reflected in the visualizations shown in a dashboard. But you can override the saved setting from within the dashboard edit panel using the "Show value labels" checkbox...

{{< figure src="dev/features/images/value-labels-dashboards.png" class="img-fluid">}}
