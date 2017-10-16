+++
date = "2017-10-16T23:20:47-04:00"
draft = false
title = "Introducing Dataset Dashboards"
description = "Dashboards provide a customizable top level view of the dataset"
weight = 20
tags = ["dashboards", "clients"]
categories = ["feature"]
+++

One of the challenges we face here at Crunch is that our tool is designed to be used by many sorts of users, who all have different needs and expectations for how they expect to interact with the data.

Our [browse](http://support.crunch.io/crunch/crunch_browsing.html) and [analyze](http://support.crunch.io/crunch/crunch_analyzing-data.html) views have proven very useful for data owners and data analysts, allowing these users to quickly find, assess, and analyze the variables they are looking for in large complex datasets.

We are proud to announce a new view that is geared towards users who might be less familiar with the details of a particular dataset, but need to see a quick summary of key analyses: the dataset dashboard.

{{< figure src="../images/dashboard.png" class="centered-image">}}

This dashboard provides a quick snapshot of up to four analyses. Double-click an analysis to open it in analyze view where you can further explore the data by [adding filters](http://support.crunch.io/crunch/crunch_filtering-data.html), [changing variables](http://support.crunch.io/crunch/crunch_analyzing-data.html), or customizing the analysis using the [display controller](http://support.crunch.io/crunch/crunch_variable-display-in-expanded-view.html).

{{< figure src="../images/dashboard-icon.png" class="floating-right">}}
The dashboard view loads when a dataset is first opened. It can be accessed by clicking the dashboard view icon at the top of the interface.

## Creating a Dashboard

If you are a dataset editor, create a dashboard using an existing deck of saved analyses by clicking the dataset name and selecting **Configure Dashboard**. See [Configuring a Dataset Dashboard](http://support.crunch.io/crunch/crunch_dashboards.html) for more information.

## The future of Dashboards
We have a number of enhancements to dashboards we plan to develop in the future, but we’d also love to hear from you: what would you like to see as part of a dataset dashboard? Let us know at support@crunch.io. Thanks!
