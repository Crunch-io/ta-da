+++
categories = ["general"]
date = "2017-08-08T21:12:10-07:00"
description = "Building software for a specific target audience can be challenging, particularly when developers' intuitions are very different from those of that audience. At a recent all-hands meeting, we exploited a unique opportunity to turn our developers into legitimate users of our product."
draft = false
tags = []
title = "Developers As Users"
weight = 20

+++

Crunch is designed to make it easy to manage and explore data, and it is particularly optimized for survey data. We natively support data types that are common in survey research, and it is also simple to do things like generate population weights and apply them automatically to all calculations. And the kinds of analyses and reports that are standard among researchers are easily selected and exported.

These features are great if you work at a research company, or in a marketing department, or otherwise work with surveys professionally. But if you're a software engineer, you live in code, not crosstabs and spreadsheets. So on the development team, we face this tension continually: we're building a product for which the target audience is not people like us. How can we best allow our team to find solutions and engage our brains fully to make the product better without letting [the inmates run the asylum](https://www.amazon.com/Inmates-Are-Running-Asylum-Products/dp/0672326140)?

{{< figure src="../images/ice-cream-display-figure.jpg" class="floating-left" attr="Ice cream eating ice cream" width="287" height="384" attrlink="https://commons.wikimedia.org/wiki/File:Ice_cream_display_figure.JPG">}}

We routinely do many things to open ourselves to our users, from discussions and screensharing with users who report bugs or request features to periodic full product demos to the team. Those are all good ways to learn more about our users and how they think, and they definitely help increase our empathy. However, there's no better way to increase empathy with the users than to become users yourself: to eat your own ice cream (also known as [eating your own dog food](https://en.wikipedia.org/wiki/Eating_your_own_dog_food), although ice cream appears to be more popular amongst our team). Under normal circumstances, though, our development team doesn't have a real reason to use our product---it's not designed to help us write software.

At our all-hands meetup a few weeks ago near Tahoe, we gave the team a special assignment: Import, clean, and analyze the [Stack Overflow developer survey](https://insights.stackoverflow.com/survey/). Find something about software developers that you think our CEO should know, and deliver results to him, all using our product. It's a great exercise because the dataset is about things developers are more likely to care about---themselves and developers like them---and it received a bit of [popular attention](https://stackoverflow.blog/2017/06/15/developers-use-spaces-make-money-use-tabs/)   [and reaction](http://evelinag.com/blog/2017/06-20-stackoverflow-tabs-spaces-and-salary/). At the same time, it's a survey---so our product should be ideal for exploring it.

# Results

The results were great. Over the next several weeks, we'll be writing more about some of the work that various people on the team did and what we found in the data. One of the fun things about the experience was seeing how different people took the open-ended prompt and ran with it in very different directions, exploiting a broad spectrum of features of the Crunch platform.

We collectively created 15 different reports that covered topics from gender representation in tech to job satisfaction internationally. These reports took many different forms: there were slide decks shared with the team in the web app, Excel workbooks exported, iPython notebooks, and data visualizations done in R. Some also created a CrunchBox, our public widget that allows our users to embed data visualizations in online articles or blog posts (like this!). Here's an example: click on the graph below to pick different variables to analyze and change the visualization settings.

<div style="text-align: center;">
<iframe src="https://s.crunch.io/widget/index.html#/ds/b877914954c7e82db199753717ddaef9/row/00001c/column/000003?viz=geo&cp=percent&dp=0&grp=stack" width="600" height="480"></iframe></div>

# What does our ice cream taste like?

Overall, we felt that our ice cream tasted pretty good! Yet, as with any fine dining experience, the difference between a good meal and an excellent meal comes down to the details in the service and presentation. We noticed a lot of little bugs and usability issues, rough edges that our everyday users know how to navigate but that stick out to an untrained new user (like us), or perhaps details that aren't quite right but that aren't critical enough that our users bother to report them. But with our attention on them, and with our inherent drive to build a better product, we not only saw them but said, "Hey, let me just fix that right now." We fixed about 20 issues in the web app and pushed a bunch of enhancements to our R and Python libraries as well.
