+++
date = "2023-10-19T15:29:45+01:00"
publishdate = "2023-10-19T15:29:45+01:00"
draft = false
title = "Introducing Enhanced Bar Plots in Crunch – Best Practice in Survey Data Visualization"
news_description = "Our Upgraded Bar Plots have been redesigned with a cleaner layout, more easily readable text, and now feature the display of confidence intervals. Click here to learn more."
description = "Our Upgraded Bar Plots have been redesigned with a cleaner layout, more easily readable text, and now feature the display of confidence intervals."
weight = 20
tags = ["graphs", "analyses", "confidence intervals"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = false
no_profiles = true
series = "main"

+++

We’re thrilled to announce a significant update that will enhance the way you visualize and interpret your survey data. Our Upgraded Bar Plots have been redesigned with a cleaner layout, more easily readable text, and now feature the display of confidence intervals.

## Why This Matters

Understanding your survey data is crucial to making informed decisions. While Crunch has always been at the forefront of providing survey analytics tools, we believe that data visualization can play a more prominent role in the research process. That’s why we've revamped our univariate bar plots to bring you an even more intuitive and insightful experience.

## What's New?

- **Confidence Intervals**: Make better-informed decisions by viewing the confidence intervals directly on the bar plots. This helps to immediately gauge the reliability of your data. See below for how to interpret these new displays.
- **Cleaner Layout**: Enjoy a more aesthetically pleasing layout that no longer tries to create huge bars that fill the whole area and instead focuses attention on the data. In particular, our horizontal bar plots make great use of the space and have smart handling for labels.
- **Improved Text Readability**: No more squinting or zooming in to read plot labels and data points. We’ve refined the text elements to make them easier to read at a glance.
- **Intelligent overflow**: Initially, only the categories that can sensibly fit on a category axis will be displayed and if there are more they can be revealed by clicking the “+x more” button. This will then allow you to scroll to see the rest.

These changes will also affect existing visualizations saved to dashboards. In some cases, you may find that slightly more or fewer categories will be visible in a dashboard tile than before due to the new use of space.

## How to interpret the confidence intervals

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/Uncertainty_on_graphs.jpg" width=600 class="img-fluid">}}


- **Look at the Range**: Each bar will have a black vertical line (the point estimate), which sits at the center of the 95% confidence interval. This range is where, given the data at hand, the actual value in the population is expected to fall in 19 out of 20 samples if the survey were repeated.
- **Check for Overlap**: If the confidence intervals of two bars overlap, it approximately means there’s not a statistically significant difference between the two groups or values you're comparing. You can see this overlap happening between Brand C and Brand D in the example above. Note, though, that statistical best practice is to not treat this significance distinction as binary. The size of the intervals and the degree of overlap are relevant (don’t hold a ruler up to the screen; that defeats the purpose of showing the whole interval).
- **Consider the Width**: The width of the confidence interval (the total range of the plus-or-minus values) can tell you a lot. A narrower interval (±2%, for example) means you can be more confident in the accuracy of the survey result than if the interval is wider (±10%).

## How to Access the New Features

The upgraded bar plots are now live and available to all users. Simply log in to your Crunch account and view or create any univariate bar plot. You'll find the new bar plots are already enabled, ready to make your data storytelling even more compelling. **Confidence intervals can be turned on using the same asterisk icon in the display controller that you already use for seeing hypothesis test colors on tables.**

## **Exporting confidence interval graphs to PowerPoint**

- When exporting a *dashboard*, graphs with confidence intervals enabled will use PowerPoint's native "Error bars" functionality to represent the confidence interval range. They don't look as nice as the Crunch ones but we want to ensure that exported visualizations remain editable, native objects, rather than static images.
- Exports from *decks*, for now, will not include the error bars. This will be addressed in a future product update.

## What’s Next?

We’re moving on to bringing these same advantages to both grouped and stacked bar plots, including being able to make targeted comparisons using click to compare, so watch this space for further announcements.

For full details of this new feature, see the [help center](https://help.crunch.io/hc/en-us/articles/20500101668365-Confidence-intervals-on-graphs).

## Your Feedback Matters

As always, we're eager to hear what you think about these enhancements. Please share your thoughts via [support@crunch.io](mailto:support@crunch.io).
