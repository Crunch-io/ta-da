+++
date = "2019-11-14T11:19:42Z"
title = "Combine all the categories from two variables"
description = "Cross one variable by another and fill all categories in 3 clicks with the new ‘combination of categories’ variable builder."
weight = 20
tags = ["analyses"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true
+++

{{< figure src="dev/features/images/interact-variable-result.png" class="float-md-right img-fluid">}}

To look in detail at your data, you sometimes need to create a variable that is the interaction of other categorical variables. You want to know not just how results differ between age groups or education level, but by age × education. The Crunch application lets you do this in just a few clicks by selecting the variables to interact — give the result a name (or accept the default of ‘x by y’) and you’re set.



{{< figure src="dev/features/images/new-variable-chooser.png" class="img-fluid">}}


To get started, click **+ New Variable** at the bottom of the variable list, and select “Create combination of categories.” Then select input variables, give it a name, and click Save. If you are a dataset editor, you can choose to share it with the whole dataset. The whole procedure is shown at reduced speed in the animation below.

{{< figure src="dev/features/images/interaction-builder.gif" class="img-fluid">}}


Interactions can only be made with categorical variables. In future releases you will be able to edit and combine results at the time of creation; now, you may need to make such adjustments after the fact by combining categories.

{{< figure src="dev/features/images/combine-interacted-variable.png" class="img-fluid">}}

We welcome your feedback at <support@crunch.io>.
