+++
date = "2021-04-09T13:27:32-04:00"
publishdate = "2021-04-09T13:27:32-04:00"
draft = false
title = "Show calculated differences between categories"
news_description = "Include net agreement, net positive rating, NPS™ calculations and more, by defining subtotals on categorical variables that calculate the difference between categories. Click here to learn more."
description = "Include net agreement, net positive rating, NPS™ calculations and more, by defining subtotals on categorical variables that calculate the difference between categories"
weight = 20
tags = ["analyses", "nets", "subtotals", "differences"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true
series = "main"

+++

You’ve been able to create subtotals in Crunch for a long time, and they’re great for quickly seeing what proportion of respondents hold similar views, such as any level of agreement with a statement or any level of liking of a brand etc. But sometimes you also need to take into account the strength of *opposing* views — those who disagree or those who dislike, and for that you want to sum those who agree and take away the sum of those who disagree, leaving you with an overall measure you can use for simple comparisons. The well-known Net Promoter Score™ measure works in this way. Crunch now supports these calculated differences and you create them in a very similar way to how you create regular subtotals:

Enter the Properties panel for a categorical variable you are allowed to edit and choose the new option called “Subtotals and differences”.

{{<figure src="https://crunch.io/dev/features/images/subtotal-differences_01.png" class="img-fluid">}}

In the next screen, you can choose between creating a subtotal (which works as it did before although it has an easier to use interface), or creating a difference. If you choose “Create difference”, you'll be presented with a screen that has the list of categories in your variable and two areas to drag categories onto.

{{<figure src="https://crunch.io/dev/features/images/subtotal-differences_02.png" class="img-fluid">}}

Simply drag any of those categories into the “positive” and “negative” areas, give your new subtotal difference a name, and click “Done”. You will now be returned to the previous screen which allows you to drag and drop the new subtotal difference to any position if you wish (the default being anchored to the top of the list). Click “Save” to commit that new subtotal difference to the variable.

This new subtotal difference will appear in bold to distinguish it from the input categories.

{{<figure src="https://crunch.io/dev/features/images/subtotal-differences_03.png" class="img-fluid">}}

To make any changes to the subtotal difference, return to that same Subtotals and differences panel and choose “edit” when hovering over the entry.

For full details of this new feature and where to find it, see the [help center](https://help.crunch.io/hc/en-us/articles/360059213452-Category-Differences).

Currently this feature is only available if you have enabled [Early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access) in your application settings.

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
