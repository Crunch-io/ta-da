+++
date = "2024-03-15T09:09:45Z"
publishdate = "2024-03-15T09:09:45Z"
draft = false
title = "Bringing the Enhanced Bar Plot capabilities to Grouped Bar plots"
news_description = "Our Grouped Bar Plots have been redesigned with a cleaner layout, more easily readable text, and now feature the display of confidence intervals. Click here to learn more."
description = "Our Grouped Bar Plots have been redesigned with a cleaner layout, more easily readable text, and now feature the display of confidence intervals."
weight = 20
tags = ["graphs", "analyses", "confidence intervals", "barplot"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = false
no_profiles = true
series = "main"

+++

With this update, our Grouped Bar Plots will enhance the way you visualize and interpret your survey data. They have been redesigned with a cleaner layout, more easily readable text, and now feature the display of confidence intervals.

## Why This Matters

Understanding your survey data is crucial to making informed decisions. While Crunch has always been at the forefront of providing survey analytics tools, we believe that data visualization can play a more prominent role in the research process. That’s why we've revamped our grouped bar plots to bring you an even more intuitive and insightful experience, bringing them in line with the enhancements already brought to univariate bar plots.

## What's New?

- **Confidence Intervals**: Make better-informed decisions by viewing the confidence intervals directly on the bar plots. This helps to immediately gauge the reliability of your data. See below for how to interpret these new displays.
- **Cleaner Layout**: Enjoy a more aesthetically pleasing layout that no longer tries to create huge bars that fill the whole area and instead focuses attention on the data. In particular, our horizontal bar plots make great use of the space and have smart handling for labels.
- **Improved Text Readability**: No more squinting or zooming in to read plot labels and data points. We’ve refined the text elements to make them easier to read at a glance.

These changes will also affect existing visualizations saved to dashboards. In some cases, you may find that slightly more or fewer categories will be visible in a dashboard tile than before due to the new use of space.

## How to interpret the confidence intervals

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/Uncertainty_on_graphs_grouped_barplot.png" class="img-fluid">}}


- **Look at the Range**: Each bar will have a black vertical line (the point estimate), which sits at the center of the 95% confidence interval. This range is where, given the data at hand, the actual value in the population is expected to fall in 19 out of 20 samples if the survey were repeated.
- **Check for Overlap**: If the confidence intervals of two bars overlap, it approximately means there’s not a statistically significant difference between the two groups or values you're comparing. You can see this overlap happening between Brand A in Segment A and Brand A in Segment B in the example above. Note, though, that statistical best practice is to not treat this significance distinction as binary. The size of the intervals and the degree of overlap are relevant (don’t hold a ruler up to the screen; that defeats the purpose of showing the whole interval).
- **Consider the Width**: The width of the confidence interval (the total range of the plus-or-minus values) can tell you a lot. A narrower interval (±2%, for example) means you can be more confident in the accuracy of the survey result than if the interval is wider (±10%).

## How to Access the New Features

The upgraded bar plots are now live and available to all users. Simply log in to your Crunch account and view or create any grouped bar plot. You'll find the new bar plots are already enabled, ready to make your data storytelling even more compelling. **Confidence intervals can be turned on using the same asterisk icon in the display controller that you already use for seeing hypothesis test colors on tables.**

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/display_controller_sig_test_bar_plots.png" width=300 class="img-fluid">}}

## **Exporting confidence interval graphs to PowerPoint**

- When exporting a *dashboard*, graphs with confidence intervals enabled will use PowerPoint's native "Error bars" functionality to represent the confidence interval range. They don't look as nice as the Crunch ones but we want to ensure that exported visualizations remain editable, native objects, rather than static images.
- Exports from *decks*, for now, will not include the error bars. This will be addressed in a future product update.

## This completes the set

We’ve now finished upgrading our line graphs, univariate bar graphs, stacked bar graphs, grouped bar graphs and donut graphs to use this new structure and functionality. We’re always looking to enhance our visualization capabilities, so watch this space!

For full details of this new feature, see the [help center](https://help.crunch.io/hc/en-us/articles/20500101668365-Confidence-intervals-on-graphs).

## Your Feedback Matters

As always, we're eager to hear what you think about these enhancements. Please share your thoughts via [support@crunch.io](mailto:support@crunch.io).
