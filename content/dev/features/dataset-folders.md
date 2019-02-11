+++
date = "2019-02-01T23:20:47-04:00"
draft = false
title = "Improved organization and navigation of Crunch datasets"
description = "We've moved to a folder-based, nested organization scheme for datasets in order to make it easier to organize, navigate, and manage permissions on datasets."
weight = 20
tags = ["organization", "datasets"]
categories = ["feature"]
images = ["https://crunch.io/img/logo-1200x630.png"]
+++

## What Are Dataset Folders?

Dataset folders allow datasets to be organized in a similar manner to a file system such as Windows Explorer or MacOS Finder. Folders make finding, organizing, and sharing data more intuitive:

* Folders can be used to organize large collections of datasets into more manageable units. If your organization imports data from many sources or has a large archive of previously imported data, you can organize them by source, time of import/survey, subject, etc.

* Editors can grant access to different folders to different sets of users. Multiple clients, or multiple groups or teams within a client, can be granted access to just the data you want to show them. Furthermore, you can move a dataset into a folder to instantly make it available to all users who have access to that folder.

These new features in turn bring some changes to our web application. Here are some key differences from the old interface.

### Navigating

#### 1. Project icons have been replaced by folders

{{< figure src="dev/features/images/folders-before-and-after.png" class="img-fluid">}}

Folders can be sorted by clicking the column headers at the top of the list.

Note that while we have removed the custom project icons from prominence in the interface for now, we will be reintroducing data branding in the near future.

#### 2. The new Shared With Me folder

Previously, any datasets that were shared with you, as well as any datasets that you had imported yourself, were bundled together in the "Personal Project". This was confusing to some, and it meant that some users' personal projects were full of lots of data that belonged elsewhere.

Now, you may see either or both of two folders, **Personal** and **Shared with Me**, pinned to the top of the folders in **All Datasets**.  

**Personal** will only appear to users who have permission to import data. It contains any datasets you have imported and not moved to another folder.

**Shared with Me** contains datasets that have been shared with you without access being granted to the folder that contains it. If no datasets have been shared with you in this way, this folder will be hidden.

If you have access to the folder that contains the dataset, it will appear in that location.

As always, when you’re not sure where to find a dataset, use the search bar at the top of screen. If you're looking for a specific dataset by name, you can narrow your search criteria to match only on dataset names.

#### 3. The header shows your current folder and how you got there

{{< figure src="dev/features/images/folders-breadcrumb.png" class="img-fluid">}}

At the top of the screen, the header now shows which folder you are currently in and the path to that folder. To jump back to a higher folder, just click on it.

See [the support page](http://support.crunch.io/articles/cEBBbgki/Navigating-Datasets-Early-Access) for more information.

### Organizing

If you are a data owner, you now have new abilities to create folders and move datasets between folders. See http://support.crunch.io/articles/ceXXoAEi/Organizing-Datasets-Early-Access for more information on these features.
