+++
date = "2017-08-21T23:20:47-04:00"
draft = false
title = "Sentiment Analysis"
description = "At the press of a button, you can classify text data with natural language processing."
weight = 20
tags = ["text", "derived variables", "sentiment analysis"]
categories = ["feature"]
+++

A wealth of information can be locked in text data. Our new “sentiment analysis” feature enables you to quantify and analyze just a bit of it: whether the text in question is on balance Positive, Neutral, or Negative — and then crosstab the derived sentiment variable just like any other variable to understand the variations among other groups in the dataset.

In the properties panel for text variables, you’ll notice the **Classify** button. Click it to create a new categorical variable containing the sentiment analysis for that text variable. Empty responses will be classified as Neutral.

{{< figure src="../images/SentimentClassify.png" class="floating-right">}}

The initial version of this feature uses a modern (slightly American inflected) English lexicon, tailored especially for terms that occur in social media:  

> [Hutto, CJ and Gilbert, E. (2014) "VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text". Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014](https://github.com/cjhutto/vaderSentiment).

We have plenty of plans for future work in this area, including other languages, a way to provide your own tailored lexicons, coding of data into a broader range of categories, specifying your own coding for text data, and more. Let us know what you’d like to see!
