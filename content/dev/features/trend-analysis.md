+++
date = "2020-12-03T14:08:05-04:00"
publishdate = "2020-12-03T19:26:13+0000"
draft = false
title = "Perform trend analysis on wave data"
news_description = "Identify trends over time by applying moving averages with just a few clicks. Click here to learn more."
description = "Identify trends over time by applying moving averages with just a few clicks."
weight = 20
tags = ["analyses", "graphs", "time series"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true

+++

In time series analysis, we want to be able to identify trends. As we collect data, random fluctuations can obfuscate a trend. *Smoothing* is an analytic process whereby we ‘iron out’ differences between time periods by taking the average of previous periods. This is also known as a *moving average.* You can now apply smoothing to your analyses with just a few clicks. In the smoothing tab accessed by clicking ⋮ select ‘One-sided moving average’ and choose the number of periods to ‘look back’ at each point.

For example, the following plots show the same data but the first shows the point estimates (unsmoothed) and the second shows a 4-period moving average.

{{< figure src="dev/features/images/trend-analysis-1.png" class="img-fluid">}}

{{< figure src="dev/features/images/trend-analysis-2.png" class="img-fluid">}}


This feature makes use of the new [categorical date variable type](https://help.crunch.io/hc/en-us/articles/360050751471-Defining-survey-wave-variables) which brings other advantages including the ability to give your own names to the date categories ("Quarter 1", "Quarter 2" etc.).

Your chosen smoothing settings are saved with your analyses when you add them to your deck, and are then reflected in both exports (Excel and PowerPoint) and on dashboards. Table coloring and column comparison are not yet available for smoothed trend estimates.

For full details of this new feature and where to find it, see the [help center](https://help.crunch.io/hc/en-us/articles/360053244351).

Currently this feature is only available if you have enabled [Early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access?) in your application settings.

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
