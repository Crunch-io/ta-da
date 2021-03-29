+++
date = "2021-03-28T11:44:48-04:00"
draft = false
title = "Crunch Automation: A blueprint for building a solid home for your data"
description = "Crunch Automation looks like a bit like SPSS syntax (and SQL commands). But that doesn’t mean that Crunch Automation serves the same function as SPSS syntax. In fact, Crunch Automation is fundamentally different in its design, philosophy and implementation. So it’s fallacious to directly compare them."
weight = 20
images = ["https://crunch.io/img/logo-1200x630.png"]
series = "main"

+++

Crunch Automation serves as a **declarative history** of transformations that have been done to a dataset. This is important to understand, because it informs you how you go about writing, running, editing and replicating datasets.

**With SPSS syntax, it**

* directly manipulates an SPSS datafile (eg: .sav file)
* is not designed with survey analysis in mind
* doesn’t set up derivations like Crunch does (it hard-codes anything you do as a new variable)
* doesn’t stay with the datafile (you keep your syntax separate from the datafile), and,
* importantly, alters your variables by overwriting the already-hard-coded variables with more syntax (which you can do endlessly)

**Crunch Automation is the opposite in these respects. It**

* works on data stored from any source (SPSS or whatever)
* is designed with survey analysis in mind (specifically with Crunch!)
* enables you to set up derived variables and artefacts (filters, multitables) - which are like calculations in the cloud
* stays with the dataset (inextricably linked to it)
* enables you to redefine the variable definitions in the first instance - so that you only declare variables once in the history

The last point is important, because it affects how you make changes to a dataset, both in tracking and ad-hoc studies. Let’s explain by example:

* You have 700 lines total of Crunch Automation to set up a dataset
* On line 80 you declare a derived variable (CREATE MULTIPLE DICHOTOMY FROM CONDITIONS)
* The dataset is in action, but you then realise you didn’t define the variable correctly. Or perhaps the research manager has *  asked for an additional subvariable to be included.

With SPSS, you would delete the variable and run-code again to redefine it. With Crunch Automation, the idea is that you go back to line 80 and fix the definition of the variable, and then re-run the script. So you **Define-Undo-Redefine**.

**What’s the advantage of the Crunch approach?**

With SPSS syntax, you end up endlessly “mutating” your code history or the variable by writing additional lines of code. You might do things in a growing body of code in multiple places for the one variable… it becomes a tangle! You are not ever 100% certain if/when a particular script(s) was run or not on a datafile. The picture over time gets even more convoluted in trackers.

Whereas in Crunch Automation, you should only ever need to change the definition of the variable ONCE around line 80. This is true in trackers where you just tweak line 80 on the next wave before append).

Perhaps an analogy can help explain. If you’ve ever worked with Adobe Photoshop, you notice that you start with a source image, and then you add “adjustment layers” that manipulate the image into the final thing you’re after. That’s a bit like what Crunch Automation does - it takes your source material (data) and then builds it up into a fully fledged dataset (which is like the output image). If you want to make a change, you can undo the layers and fix a deeper layer, before reapplying the layers.

This is in contrast to SPSS syntax, where it’s a bit more like working in Windows default Paint program - you directly change the pixels and there’s no layering approach. In fact, there’s not really an undo function either - you’d need to make sure you had saved a version before any changes, and then hope your syntax log re-runs OK.

**Crunch Automation is a solid blueprint for your dataset**

Crunch Automation builds things up like a house - following the path of the Definitive Guide.
The schema commands are like the concrete foundation (the first layer). Creating variables are like the structural pillars and the walls. Organizing variables (folde allocation) ensures everything is in the right room. Artefacts (multitables, filters, decks, dashboards) are like the soft furnishings - cushions, artworks, furniture. Once your house (schema) is complete, then people can come through the house (these are the respondents or cases in the data).

If you want to make a change to your house, the blueprint, you should unwind your house, make the change, and then build it up again. That way your house stays solid, simple and beautiful. The alternative (SPSS way) is fiddling with your house with endless renovations. Before long the house looks a mess and no one wants to stay!

We’ll have more to say on this matter, but we welcome your comments and feedback. Please log them below and we’ll answer in a Q&A.
