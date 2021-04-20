+++
date = "2021-03-05T11:44:48-04:00"
draft = false
title = "Great new visualizations for time-series analyses and trackers"
news_description = "Crunch now has a completely redesigned time plot that offers confidence bands, smoothing, and custom selection of categories to show/hide. Click here to learn more."
description = "Crunch now has a completely redesigned time plot that offers confidence bands, smoothing, and custom selection of categories to show/hide."
weight = 20
tags = ["time-series", "analytics", "visualizations", "trackers"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true
series = "main"

+++

Line graphs are great at showing how values are changing over time and therefore ideal for tracking studies. Crunch's line graphs have been completely redesigned to offer some great new features as well as improved usability and flexibility.

**Category selection**

Line graphs become really hard to read when there are lots of lines shown simultaneously, so Crunch now defaults to showing just the top 5, but you can pick whichever combination of lines (including showing more or fewer than 5) from the new "Select categories" interface. This allows you to show just the lines that tell your chosen data story. And your selection is then reflected in PowerPoint exports and dashboards.

{{<figure src="dev/features/images/new-time-plot_01.gif" class="img-fluid">}}

**Confidence bands**

Crunch's line graphs now support the display of confidence bands, calculated at 95% confidence, and you can turn these on or off with the click of the * asterisk button.

{{<figure src="dev/features/images/new-time-plot_02.gif" class="img-fluid">}}

**Draggable bar**

As well as being able to hover over points to see their values, there's a vertical bar that you can drag to any point in the time-series to see all the values and ranking at that point in time.

{{<figure src="dev/features/images/new-time-plot_03.gif" class="img-fluid">}}

**Smoothing**

Smoothing, also known as "moving averages" or "rolling averages", has been available for the existing line graph component for a little while, thanks to the new "Categorical date variables", but works here too. Click [here](https://help.crunch.io/hc/en-us/articles/360053244351-Time-series-smoothing-moving-average-) to read more about the new Smoothing feature.

**Editable labels**

Another advantage of using categorical variables with the new date attribute is that you now have control over the labels that are displayed for the x-axis. So if you want to call them something more meaningful to you (or your client) such as "Wave 17" or "Extra Christmas boost" then you can.

For full details of this new feature and where to find it, see the [help center](https://help.crunch.io/hc/en-us/articles/360057226852-Time-series-analysis-with-time-plots).

Currently this feature is only available if you have enabled [Early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access) in your application settings.

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
