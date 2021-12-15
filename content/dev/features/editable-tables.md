+++
date = "2020-08-31T09:26:59-04:00"
publishdate = "2020-08-31T14:20:33+0000"
draft = false
title = "Customize your tables for export or dashboards"
news_description = "Anyone can now customize their tables for export or dashboards by hiding rows/columns, reordering rows/columns and editing labels. Click here to learn more."
description = "Users can now customize their tables for export or dashboards by hiding rows/columns, reordering rows/columns and editing labels."
weight = 20
tags = ["analyses", "dashboards"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = false
no_profiles = true

+++

You've already been able to customize saved *graphs*, but now you can make those same edits to the rows and columns of saved tables, either for export or for display in dashboards. More specifically, you can now...

1. Hide any rows and/or columns of a table, including calculated rows/columns such as subtotals, leaving only those you want your export/dashboard consumers to see. Simply uncheck the box next to the row/column to hide it.
2. Reorder the rows/columns of a table, just by dragging them into their new order.
3. Rename any row/column just by typing into the name box. Great for cases where the labels are too long or contain unwanted content.

Together, these features allow you to turn off rows and columns in 'messy' tables. For example, the table below has many columns that the researcher may not want to display in the analysis. They may want to focus the viewer's attention on what's most important.

{{< figure src="dev/features/images/editable-table.png" class="img-fluid">}}

The result is something like the below - which is much neater.

{{< figure src="dev/features/images/editable-table-tidy.png" class="img-fluid">}}

The action here simply hides the rows and columns in the table - the original variable is unaffected (so if you made another table, you would see all the columns/rows again).

All users can access this new functionality via the "edit" link shown upon hover of each slide saved to the deck.

{{< figure src="dev/features/images/editable-from-deck.png" class="img-fluid">}}

Editors can additionally access this functionality when editing dashboard tiles that contain tables.

The following video walks you through the steps for adding a table to your deck and then how to edit that table to only show the rows and columns of interest, arranged in the desired order.

<div class='embed-container'><iframe src="https://player.vimeo.com/video/451935697" frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe></div>

See [the help center](https://help.crunch.io/) for more information on these features.

We'd love your feedback at [support@crunch.io](mailto:support@crunch.io).
