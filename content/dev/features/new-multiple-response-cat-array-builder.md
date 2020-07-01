+++
date = "2020-07-01T15:16:25-04:00"
title = "Easily create and recombine categorical arrays and multiple response variables"
news_description = "Create your own custom combinations to use in both categorical arrays and multiple response variables — available now with Early Access enabled. Click here to learn more."
description = "Users can now combine variables with common categories to analyze together as a group, and summarize arrays by choosing categories of interest."
tags = ["analysis, multiple response, categorical array, variables"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
labs_only = true
no_profiles = true
+++

Array variables allow you to analyze together a set of variables that share a common structure and theme. For example, surveys often ask respondents to use a common scale to rate or respond to different prompts, sometimes in a grid, all sharing a common set of response categories. When analyzing the data, a categorical array variable lets users see all the items together. This structure allows users to easily compare lists of brands against a common set of attributes, or compare a set of statements against a common agreement scale — something that is much harder to do with distinct categorical variables. Categorical arrays are displayed as two-dimensional tables or stacked graphs by default in Crunch, letting you compare the complete distribution between items.

A multiple response variable is a kind of _summary_ of the items or input variables in a categorical array. In its simplest form, responses take the form of either “selected” or “not selected”. Crunch uses this form (called “multiple dichotomies”) to represent survey questions where respodents can select multiple answers from a list of responses (“Choose all that apply”) — each response in the data is a separate variable, but for analysis, they need to be grouped together into a multiple response variable.

Multiple response variables in Crunch allow you to choose more than one selected category, so you can also summarize an array of “level of agreement” into a multiple response view of the percentage who selected either “Agree” or “Strongly agree”. Multiple response variables are displayed as a ‘flattened’ form of a categorical array, allowing you to analyze this more condensed, crossing it by demographics or trending over time, etc. 

The following videos demonstrate how to use these new builders. First, we create a new Categorical Array from a group of single-response variables that have a common set of answer categories.

<video style="width: 100% !important; height: auto !important; margin: 20px 0;" src="dev/features/videos/Creating_a_Categorical_Array_from_single-response_variables.mp4" controls></video>

Then, we create a simplified multiple response variable from a subset of those items of interest.

<video style="width: 100% !important; height: auto !important; margin: 20px 0;" src="dev/features/videos/Creating_a_Multi-Response_as_a_subset_of_a_Categorical_Array.mp4" controls></video>

Note: Currently this feature is only available if you have enabled [early access](https://help.crunch.io/hc/en-us/articles/360040465331-How-to-enable-early-access).

To find out more about the new variable builders, you can read about them on our help page [here](https://help.crunch.io/hc/en-us/articles/360040481451-Creating-multiple-response-and-categorical-arrays).

We’d love your feedback at [support@crunch.io](mailto:support@crunch.io).
