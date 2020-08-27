+++
date = "2020-08-26T14:47:45-04:00"
publishdate = "2020-08-26T21:13:44+0000"
draft = false
title = "Combine categories in dashboard filter variables"
news_description = "Editors can now choose to allow dashboard users to make multiple selections within dashboard “Groups” variables — e.g. “Midwest” and “West” selected simultaneously, thereby creating a filter that includes everyone in either of these regions. Click here to learn more."
description = "Editors can now choose to allow dashboard users to make multiple selections within dashboard “Groups” variables — e.g. “Midwest” and “West” selected simultaneously, thereby creating a filter that includes everyone in either of these regions."
weight = 20
tags = ["analyses, dashboards, groups, filters"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true

+++

The Groups on dashboards can now optionally allow multiple category selections to effectively combine categories in the filter. Dashboard editors can set an option on the configuration screen for dashboard “Groups” that allows users to make multiple selections within each variable. For example, if you choose an age categories variable as a group and turn on this new option, the dashboard users will be able to select both “18–24” and “25–34” simultaneously, thereby creating a filter that includes anyone aged 18–34.

The new option can be found at the top of the Edit Groups panel.

{{< figure src="dev/features/images/selection-within-groups.png" class="img-fluid">}}

The default is single selection, but with multiple selection enabled, the user is able to create group definitions.

{{< figure src="dev/features/images/multiple-selection-in-groups-sidebar.png" class="img-fluid">}}

As before, you can click the “×” to remove a category from your selection or click “Reset Groups” at the bottom of the panel to clear all group filtering.

For full details, see the [help center](https://help.crunch.io/hc/en-us/articles/360040053432-How-to-apply-filters-to-a-dataset-dashboard).  

Currently this feature is only available if you have enabled ‘[Early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access)’ in your application settings.

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
