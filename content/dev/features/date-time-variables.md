+++
date = "2021-08-17T16:52:04-04:00"
publishdate = "2021-08-17T16:52:04-04:00"
draft = false
title = "Crunch's new visualizations for time-series analyses and trackers are now extended to Date-Time variables"
news_description = "Crunch's completely redesigned time plot that offers confidence bands and custom selection of categories to show/hide is now available for all line graphs. Click here to learn more."
description = "Crunch's completely redesigned time plot that offers confidence bands and custom selection of categories to show/hide is now available for all line graphs."
weight = 20
tags = ["analyses", "graphs", "time series"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true
series = "main"

+++

Back in April this year, we announced that a great new visualization was available for time series analyses that used the new "Categorical Date" variable type. Existing time plots that used the older Date-Time variable type were unaffected and continued to use the previous line graph component. Since then, we've worked to extend the new line graph functionality to those original Date-Time variables so that everyone can benefit from their better design and functionality, and we can now announce that *all* time plots will be using the new visualization. Below you will find a summary of what you can expect from your new time plots in Crunch.

**Category selection**

Line graphs become really hard to read when there are lots of lines shown simultaneously, so Crunch now defaults to showing just the top 5 for newly created analyses, but you can pick whichever combination of lines (including showing more or fewer than 5) from the new "Select categories" interface. This allows you to show just the lines that tell your chosen data story. And your selection is then reflected in PowerPoint exports and dashboards.

{{<figure src="https://crunch.io/dev/features/images/date-time-variables_01.gif" class="img-fluid">}}

Existing line graphs, saved to decks or used in dashboards, will have their current set of lines preserved so you won't see any changes to the lines shown.

**Confidence bands**

Crunch's line graphs now support the display of confidence bands, calculated at 95% confidence, and you can turn these on or off with a click of the * asterisk button.

{{<figure src="https://crunch.io/dev/features/images/date-time-variables_02.gif" class="img-fluid">}}

<div id="draggable" style="padding-top:80px;"></div>

**Draggable bar**

As well as being able to hover over points to see their values, there's a vertical bar that you can drag to any point in the time-series to see all the values and ranking at that point in time.

{{<figure src="https://crunch.io/dev/features/images/date-time-variables_03.gif" class="img-fluid">}}

Note that there are two benefits *not* available for Date-Time analyses because they rely on the new Categorical Date variable type: Smoothing (a.k.a. "Rolling averages") and editable time-axis labels. There is therefore still good motivation for using Categorical Date variables in your projects. You can read more about the smoothing feature [here](https://help.crunch.io/hc/en-us/articles/360053244351-Time-series-smoothing-moving-average-) and about the editable labels [here](https://help.crunch.io/hc/en-us/articles/360050751471-Defining-survey-wave-variables).

For full details of this new feature and where to find it, see the [help center](https://help.crunch.io/hc/en-us/articles/360057226852-Time-series-analysis-with-time-plots).

Currently this feature is only available if you have enabled [Early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access) in your application settings.

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
