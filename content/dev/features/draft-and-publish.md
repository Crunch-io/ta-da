+++
date = "2017-06-12T23:20:47-04:00"
draft = false
title = "Deliver New Data When You’re Ready"
description = "Our new draft-and-publish feature allows you to prepare and review changes to data before pushing them to everyone."
weight = 20
tags = ["draft and publish", "clients"]
categories = ["feature"]
+++

Lately we’ve been focusing on ways to make it easier for data owners to manage data for their clients. After all, Crunch isn’t just for analyzing data, it’s a tool for making everything about delivering data to clients faster, smoother, and more powerful.

To that end, we’ve recently developed a draft and publish feature that allows data owners to make significant changes to data accessible to their clients with minimal interruption to how those clients interact with the data. Here’s how it works.

## Creating a Draft

{{< figure src="../images/DraftButton.png" class="floating-left">}}

Open dataset properties of a dataset you are currently editing; you’ll see the Draft button on the right side of the screen.

Click **Create Draft** to create and open a draft of the current dataset. Now you can append new rows of data, reorganize variables, create new variables, and edit dataset and variable metadata freely, and your clients won’t see your changes until you are ready. The draft dataset is automatically made available to others who have edit permissions on the current dataset, so multiple editors can make changes collaboratively or allow other stakeholders to review and sign off on changes. Other editors will see the draft marked with the **draft** label.

{{< figure src="../images/DraftDsList.png" class="centered-image">}}

While a draft exists, we prevent the original and draft datasets from getting out of sync by warning anyone who attempts to edit the original and pointing them to the draft. Additionally, if you find that you are not happy with the changes you’ve made, you can simply delete the draft dataset and start over again by creating a new draft.

## Publishing

{{< figure src="../images/PublishButton.png" class="floating-right">}}

Once you are satisfied with the draft, your changes can be published by returning to dataset properties in the draft and clicking **Publish**. The original dataset will be updated with the changes from the draft and the draft will be deleted.

We are confident this feature will make managing data for your clients a better experience for you and for them. If you have any feedback about draft and publish (or anything else!), please don’t hesitate to let us know at [support@crunch.io](mailto:support@crunch.io).
