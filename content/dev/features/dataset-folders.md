+++
date = "2019-02-10T23:20:47-04:00"
draft = false
title = "Improved Organization of Crunch Datasets"
description = "We've moved to a folder-based, nested organization for datasets in order to make it easier to navigate and manage permissions on datasets."
weight = 20
tags = ["organization", "datasets"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
+++

Dataset folders allow you to organize your data hierarchically, similar to a file system as you might see in Windows Explorer or MacOS Finder. Folders make finding, organizing, and sharing data more intuitive.

* Folders can be used to organize large collections of datasets into more manageable units. If your organization imports data from many sources or has a large archive of previously imported data, you can organize them by source, time of import/survey, subject, etc.

* Editors can grant access to different folders to different sets of users. Multiple clients, or multiple groups or teams within a client, can be granted access to just the data you want to show them. Furthermore, you can move a dataset into a folder to instantly make it available to all users who have access to that folder.

These new features in turn bring some changes to our web application. Here are some key differences from the old interface.

## Navigating

The first thing you'll notice is that the stripe of icons at the left have been replaced by folders. The flat list of project icons didn't work well with a model where folders could nest within each other, so we changed the display to more closely match the underlying model. (Note that while we have removed the custom icons from display for now, we will be reintroducing them with additional branding settings in the near future.)

{{< figure src="dev/features/images/folders-before-and-after.png" class="img-fluid">}}

Click on a folder's name to enter it. When you do, you'll see at the top of the screen the folder you are currently in and the path to that folder.

{{< figure src="dev/features/images/folders-breadcrumb.png" class="img-fluid">}}

To jump back to a higher folder, just click on it in the header.

Within a folder, you can sort the list of datasets and folders by clicking the column headers at the top of the list. By right-clicking on the header, you can customize which columns appear in the list, so you can sort the view by most-recently accessed, or alphabetical, or whatever you want.

The other major change to navigation involves the "Personal Project".
Previously, any datasets that were shared with you, as well as any datasets that you had imported yourself, were bundled together in the personal project. This was confusing to some, and it meant that some users' personal projects were full of lots of data that belonged elsewhere.

We've simplified where datasets are presented in folders to you. If you have access to a folder, you'll see that listed at the top level, and everything contained inside that folder will show up inside that folder. **Personal** now contains any datasets you have imported and not moved to another folder. Only users who have permission to import data will see Personal. The other special folder, **Shared with Me**, contains datasets that have been shared with you without access being granted to the folder that contains it. If no datasets have been shared with you in this way, this folder won't appear.

As always, when you’re not sure where to find a dataset, use the search bar at the top of screen. If you're looking for a specific dataset by name, you can narrow your search criteria to match only on dataset names.

For more details on navigating dataset folders, see [the support page](http://support.crunch.io/articles/cEBBbgki/Navigating-Datasets-Early-Access) for more information.

## Organizing

If you are a data owner, you now have new abilities to create folders and move datasets between folders. See [the help site](http://support.crunch.io/articles/ceXXoAEi/Organizing-Datasets-Early-Access) for more information on these features.
