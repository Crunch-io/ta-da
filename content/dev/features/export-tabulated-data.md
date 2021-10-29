+++
date = "2021-10-29T16:52:54-04:00"
publishdate = "2021-10-29T16:52:54-04:00"
draft = false
title = "Export Crunch survey results in a BI-ready format"
news_description = "New tabulated data export format for multitables. Click here to learn more."
description = "New tabulated data export format for multitables."
weight = 20
tags = ["tabulated data", "export", "csv"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true
series = "main"

+++

**Crunch gives you the best of all worlds** — you analyze all your survey data in Crunch, and now you can export those results into your other reporting tools (such as Tableau, Google Data Studio, PowerBI) so that you can see your survey results alongside your other business metrics.

Your tables (tab books) can now be exported in a specialized output format. This format contains a row for each cell of the table you see in the Crunch app. For example, this table from Crunch would generate 40 rows. There will be a row for the “All” category for “I am making more sustainable choices….” response, one for males and more sustainable choices, females and more sustainable choices, etc. all the way down to the 55+ age group and “Don’t know”.

{{<figure src="https://crunch.io/dev/features/images/export-bi-ready-format-1.png" class="img-fluid">}}

The output format is a delimited text file of results that is ready to put into other analysis and presentation tools. Below is an excerpt of the file generated from the table above:

{{<figure src="https://crunch.io/dev/features/images/export-bi-ready-format-2.png" class="img-fluid">}}

{{<figure src="https://crunch.io/dev/features/images/export-bi-ready-format-3.png" class="img-fluid">}}

You have a few options to customize your file (noted below).

To generate your file, navigate to your multitable. In the upper right hand corner, click **Export** and select **Export settings** from the dropdown menu.

{{<figure src="https://crunch.io/dev/features/images/export-bi-ready-format-4.png" class="img-fluid">}}

This screen will appear:

{{<figure src="https://crunch.io/dev/features/images/export-bi-ready-format-5.png" class="img-fluid">}}

You can customize the format and contents of the export. Column headings (the first row of the exported file) can be compact, single-word labels or space-separated labels. Columns can be separated by commas or semicolons; and decimals by a period or comma. After making your customizations, click Save to persist them.

To export, click **Export** again in the upper-right and select **Export tab book** from the dropdown menu. Select the **CSV** option from the **Format** menu, choose which variables to export, and then click **Export** to download your results.

Once you’ve downloaded your tabulated results file, consult the documentation on the tool of your choice for guidance on how to upload. Below we show you how our sustainability results look in Google Data Studio.

{{<figure src="https://crunch.io/dev/features/images/export-bi-ready-format-6.png" class="img-fluid">}}

Details regarding this new feature can be found in the [help center](https://help.crunch.io/hc/en-us/articles/4412334662157-Export-tabulated-data).

Currently, this feature is only available for [early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access) users.

Questions or feedback on this feature? Please contact [support@crunch.io](mailto:support@crunch.io) and use “Tabulated results export” in the subject line.
