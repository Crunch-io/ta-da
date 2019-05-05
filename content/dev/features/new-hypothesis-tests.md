+++
date = "2019-05-04T23:20:47-04:00"
title = "New hypothesis testing features in Crunch"
news_description = "Crunch tab book exports now include a new hypothesis testing option that computes all possible comparisons between columns of a two-way table. Click here to learn more."
description = "Crunch tab book exports now include a new hypothesis testing option that computes all possible comparisons between columns of a two-way table."
weight = 20
tags = ["tab books", "export", "xlsx"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
no_profiles = true
+++

Crunch tab book exports now include a new hypothesis testing option that computes all possible comparisons between columns of a two-way table. When users select the "Column t-test" option in the “Export tab book… > Customize” panel, columns in output will be lettered and differences that are significant at the .05 significance level are indicated by letters underneath the cell with the higher percentage. [See here for details](http://support.crunch.io/articles/c9e4yRRi/Hypothesis-testing-in-Crunch).

{{< figure src="dev/features/images/tab-book-export-panel.png" class="img-fluid">}}

An example of the exported result is shown below.

{{< figure src="dev/features/images/example-tab-book-output.png" class="img-fluid">}}


A way to perform the same tests in the web application is under development and is expected to be released later in the second quarter of 2019.
