+++
date = "2021-06-22T11:29:37-04:00"
publishdate = "2021-06-22T11:29:37-04:00"
draft = false
title = 'Add subtotals (a.k.a. "nets") to your multiple response variables'
news_description = "Simplify your analyses to get the insights you need with fewer distractions. Click here to learn more."
description = "Simplify your analyses to get the insights you need with fewer distractions."
weight = 20
tags = ["analyses", "nets", "subtotals", "differences"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true
series = "main"

+++

Dataset editors have been able to add subtotals (a.k.a. “nets”) to categorical and categorical array variables for a long time, but this hasn’t been the case for multiple response variables. There are many applications for subtotals on multiple response variables — a common one is a group of products or sub-brands within a brand, or a grouping of statements into themes. Previously, users had to define new variables with often complex logic to describe each combination, and then hide the input variable. Now, Crunch provides a way to specify combinations of items directly on multiple response variables. And even better, these subtotal categories will appear on graphs in Crunch, including on time-series graphs.

The method of creating multiple response variable subtotals is the same as the method for creating categorical variable subtotals.

- Open the **Properties** panel for a variable and choose the new **Subtotals** button.
- In the screen that appears, click **Create subtotal**.
- Drag the categories that you want to combine into the dropzone and give the subtotal a name.
- Click save.

You can then reposition the subtotal to somewhere other than the top if you wish. If you choose to position the subtotal at the top or the bottom then it will stay in this position, but if you move the subtotal to somewhere else in the list then this will attach it to the category immediately above it and the subtotal will then be kept immediately below that anchor category as the list is sorted. From this screen, you can also delete the subtotal or click **edit** to make changes to the subtotal’s definition or its name.

Once you’ve saved your subtotals, you will see them added in bold to the variable. Note that this is a change made to the original variable, and therefore will be visible to all users of the dataset. That's why it's only available to dataset editors.

For full details of this new feature, see the [help center](https://help.crunch.io/hc/en-us/articles/360050364772-Category-Subtotals).

Currently this feature is only available if you have enabled [Early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access) in your application settings.

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
