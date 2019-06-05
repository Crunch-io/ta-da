+++
date = "2019-06-04T23:20:47-04:00"
title = "Click to set the comparison column for hypothesis tests"
news_description = "You can now click to set a reference column for hypothesis testing in tables. Click here to learn more."
description = "Tables are shaded to show which other columns are higher or lower than the reference column for each row."
weight = 20
tags = ["tables", "statistics"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
+++

Tables in the application now let you set a column as the basis of comparison, shading the table to show which other columns are higher or lower than the reference column, and to what level of statistical significance. The test is a two-tailed _t_ test comparing each column proportion in turn to the proportion in the reference column. In a multitable, the test is conducted between categories within each column variable, and not across column variables. [See here for more details](http://support.crunch.io/articles/c9e4yRRi/Hypothesis-testing-in-Crunch).

{{< figure src="dev/features/images/compare-columns.gif" class="img-fluid">}}


{{< figure src="dev/features/images/set-comparison-1.png" class="img-fluid">}}
