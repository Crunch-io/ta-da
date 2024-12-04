+++
date = "2024-09-05T17:12:10+01:00"
publishdate = "2024-09-05T17:12:10+01:00"
draft = false
title = "New graph customizations for dashboard display"
news_description = "Ever wanted to hide the gridlines or the numeric axis for a cleaner look? Ever wanted to add in confidence bands after saving? Now you can customize your saved visualizations to get the dashboard display you want. Click here to learn more."
description = "Crunch now gives you more control than ever before over how your graphs are displayed in dashboards, as well as a more logical arrangement of controls across tabs."
weight = 20
tags = ["analyses", "dashboard", "graphs"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = false
no_profiles = true

+++

## How it works

When editing a dashboard, you already have access to lots of great customizations via the existing tabs of the “Edit Tile” interface – Properties, Categories and Colors. For most visualization types, you’ll now find a fourth tab – Options.

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/options_tab.png" class="img-fluid center">}}

## The new Options tab

The contents of this tab will include most of the following options, though the actual set will vary depending on the visualization type you’re working with.

Some are new options not previously available while others are options that have been moved to this tab for consistency.

## New options

**Hide value axis**
<div class="container">
  <div class="row">
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-01.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Default - value axis shown</figcaption>
    </div>
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-02.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Value axis hidden (and “Show values” enabled)</figcaption>
    </div>
  </div>
</div>

We would recommend always enabling “Show values” if you hide the value axis, otherwise it will be hard for your users to interpret the visualization.

**Hide gridlines**

<div class="container">
  <div class="row">
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-03.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Default - gridlines shown</figcaption>
    </div>
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-04.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Gridlines hidden</figcaption>
    </div>
  </div>
</div>

**Hide connecting bars**

When confidence intervals are enabled for bar graphs, those intervals are connected to the category axis with thin bars. You can now hide these connecting bars if you prefer.

<div class="container">
  <div class="row">
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-07.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Default - connecting bars shown</figcaption>
    </div>
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-08.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Connecting bars hidden</figcaption>
    </div>
  </div>
</div>

**Category axis label position (horizontal bars only)**

<div class="container">
  <div class="row">
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-09.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Default - category axis labels outside the plot</figcaption>
    </div>
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-10.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Category axis labels run along the bar length</figcaption>
    </div>
  </div>
</div>

## Existing options

**Show values**

<div class="container">
  <div class="row">
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-11.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Default - no values shown</figcaption>
    </div>
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-12.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">With values displayed</figcaption>
    </div>
  </div>
</div>

**Value axis - Min and Max**

<div class="container">
  <div class="row">
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-05.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Default - dynamic numeric axis range</figcaption>
    </div>
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-06.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Max set to 100 (as an example)</figcaption>
    </div>
  </div>
</div>

**Fit to tile**

<div class="container">
  <div class="row">
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-13.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Default - bars sized to ‘best practice’ proportions</figcaption>
    </div>
    <div class="col-md-6">
      {{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/bar-customization-option-14.png" class="img-fluid-col-2 max-width-img-md">}}
      <figcaption class="img-caption">Bars spaced and sized to use the available tile area</figcaption>
    </div>
  </div>
</div>

In addition to the new customizations available in the Options tab, “Show confidence bands” has now been added to the Properties tab. This will allow you to enable or disable confidence bands on visualizations even after having saved them to a deck or dashboard.

{{<figure src="https://player-crunch-io.s3.amazonaws.com/help-crunch-io/screenshots/show_confidence_bands_checkbox.png" class="img-fluid center">}}

## Try it out today

For full details of this new feature, see the [help center](https://help.crunch.io/hc/en-us/articles/9414277417741-Customizing-dashboards-and-dashboard-tiles#h_01J3XVABPZWWMTWAJS4RZY23F8).

## Your Feedback Matters

As always, we're eager to hear what you think about these enhancements. Please share your thoughts via [support@crunch.io](mailto:support@crunch.io).
