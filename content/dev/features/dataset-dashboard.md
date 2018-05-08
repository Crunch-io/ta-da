+++
date = "2017-10-17T23:20:47-04:00"
draft = false
title = "Introducing Dashboards"
description = "Dashboards provide a clear top-level view of a dataset. Dataset owners can easily customize the contents of the dashboard in order to provide a concise, beautiful summary of key findings."
weight = 20
tags = ["dashboards", "clients", "graphs"]
categories = ["feature"]
images = ["https://crunch.io/img/og-image.png"]

+++

Crunch is designed to make data accessible to many different audiences that have varying needs, expectations, and technical abilities.
Our [browse](http://support.crunch.io/crunch/crunch_browsing.html) and [analyze](http://support.crunch.io/crunch/crunch_analyzing-data.html) views allow data owners and analysts to quickly explore and analyze interesting insights in potentially large, complex datasets. However, not everyone has time to explore a dataset---some need to see key findings at a glance.

To meet this executive-type need, we're introducing a new dashboard feature.

{{< figure src="dev/features/images/dashboard.png" class="img-fluid" width="100%">}}

This dashboard provides a quick view of up to four analyses, right when you open a dataset. These views are dynamic: when new data is added to the dataset, the dashboard updates with the latest values.

In keeping with Crunch's philosophy that exploring data should be instant and intuitive, the graphs and tables on a dashboard can be a starting point for further analysis if you want to dig deeper. Double-click on an analysis to open it in the full-screen view, where you can explore by [adding filters](http://support.crunch.io/crunch/crunch_filtering-data.html), [changing variables](http://support.crunch.io/crunch/crunch_analyzing-data.html), or customizing the analysis using the [display controller](http://support.crunch.io/crunch/crunch_variable-display-in-expanded-view.html).

{{< figure src="dev/features/images/dashboard-icon.png" class="float-right">}}
At any time when working with a dataset, you can return to the dashboard by clicking its icon at the top of the screen.

## Creating a Dashboard

If you are a dataset editor, setting up a dashboard for your dataset takes just a few steps. First, [save the analyses](http://support.crunch.io/crunch/crunch_saving-analyses.html) you want to appear in the dashboard to a deck. Then, indicate that you want to use that deck as the source for your dashboard by clicking the dataset name, selecting **Configure Dashboard**, and select the deck. See [Configuring a Dataset Dashboard](http://support.crunch.io/crunch/crunch_dashboards.html) for more information. To change the composition of the analyses that show in the dashboard, edit the saved slides in your deck, and the changes will be reflected in the dashboard.

## The Future of Dashboards

There are lots of enhancements we plan to add to the dashboards, and your feedback about how you'd like to see them improved is greatly appreciated. Let us know what you think at support@crunch.io.
