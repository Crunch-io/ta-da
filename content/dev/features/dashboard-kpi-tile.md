+++
date = "2019-12-10T11:12:18-04:00"
draft = false
title = "Adding KPI tiles to dashboards"
news_description = "Dataset editors can add KPI tiles to a dashboard to display a single value from a table to highlight or track a specific key metric. Click here to learn more."
description = "Dataset editors can add KPI tiles to a dashboard to display a single value from a table to highlight or track a specific key metric."
weight = 20
tags = ["dashboards"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true

+++

Dashboards can now contain KPI analyses that take a single value from a table and present it in a tile. Great for when there's a key metric you want to highlight or track.

{{< figure src="dev/features/images/dashboard-kpi.png" class="img-fluid">}}

Dataset editors can now add KPI analyses like these to dashboards. This allows you to show a key company metric – e.g. Brand Awareness – as a prominent value that grabs attention.

To create one, simply save an analysis of any kind – table, chart or variable card – that contains the value you want to show as a KPI. Then, in edit mode of the dashboard, enter the "Edit" view (only available to dataset editors) and enter the properties panel for that particular analysis. Change that visualization type to KPI...

{{< figure src="dev/features/images/dashboard-kpi-icon.png" class="img-fluid">}}

... and then select the value you want to use as a KPI from the table...

{{< figure src="dev/features/images/dashboard-kpi-selection.png" class="img-fluid">}}

Make optional changes to the titles, number type and decimal places, and click Save.
KPI tiles can be moved and resized like other tiles, but they have a maximum size of 4x4 cells.

Full support documentation can be found [here](url).

As an added bonus, editors can now also switch between tables and graphs when editing dashboards, as well as change the basic metadata (titles, description etc) for tiles that contain tables.

We'd love your feedback at <support@crunch.io>.
