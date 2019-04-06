+++
date = "2019-04-05T23:20:47-04:00"
title = "Column t-tests in Tab Books"
description = "Show significant differences in tab books"
weight = 20
tags = ["exports", "tab books"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
+++

## Customize tab books
{{< figure src="dev/features/images/customize-tab-book-panel.png" class="img-fluid">}}

Crunch tab book exports show whether the difference in percentages between pairs of columns are significant at the .05 level. Columns are labelled with letters. Below or beside the percentage in each cell will be a letter indicating that the percentage in that cell is higher than the percentage in the column with that letter. We use a two-tailed t-test. In addition, you can choose ‘long’ or ‘wide’ arrangement of the measures in each cell.

To enable the t-test letters, check the “Column t-tests” field in the panel shown above, found under Export tab book > Customize.

This feature is now available if you have [‘Early access’](http://support.crunch.io/articles/yTyz6ArT/How-to-enable-early-access) enabled in the app. We’re eager for feedback, so please try it and let us know how we can improve it.
