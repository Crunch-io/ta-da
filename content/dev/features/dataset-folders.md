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

To jump back to a higher folder, just click on it in the header.

{{< figure src="dev/features/images/folders-breadcrumb.png" class="img-fluid">}}

Within a folder, you can sort the list of datasets and folders by clicking the column headers at the top of the list. Right-click on the header to select which sortable columns appear in the list.

The other major change to navigation involves the **Personal** folder, previously called the **Personal Project**. This folder used to contain any datasets that were shared with you as well as any datasets that you had imported yourself, which for some users resulted in a long list of datasets with no clear logic grouping them together.

With this update, we've simplified where you can find the data you have access to.

* If you have access to a folder, you'll see it listed under **All Datasets**, and everything contained inside that folder (including other folders) will be available inside that folder.
* **Personal** now contains any datasets you have imported and not moved to another folder. Only users who have permission to import data will see the Personal folder.
* The other special folder, **Shared with Me**, contains datasets that have been shared with you without access being granted to the folder that contains it. If no datasets have been shared with you in this way, this folder won't appear.

The **Personal** and **Shared with Me** folders will be pinned to the top of the **All Datasets** list to allow them to be easily found and accessed.

As always, when you’re not sure where to find a dataset, use the search bar at the top of screen. If you're looking for a specific dataset by name, you can narrow your search criteria to match only on dataset names.

For more details on navigating dataset folders, see [the support page](http://support.crunch.io/articles/cEBBbgki/Navigating-Datasets-Early-Access) for more information.

## Organizing

If you are a data owner, you can create folders, move datasets between folders, and grant other users access to a specific folder.

To create a folder, click the dataset name and select **New Folder** from the dropdown.

{{< figure src="dev/features/images/folders-add-folder.png" class="img-fluid">}}

This opens the **New Folder** dialog, where you can name the new folder.

{{< figure src="dev/features/images/folders-create-folder.png" class="img-fluid">}}

To move a dataset or folder to a new folder, hover over it in the dataset list, click the down-arrow to open a dropdown, and select **Move to...**.

{{< figure src="dev/features/images/folders-move-to-menu.png" class="img-fluid">}}

This opens the **Move to** dialog that you can use to move the selected dataset or folder to any folder where you have write access (including your **Personal** folder).

{{< figure src="dev/features/images/move-to-dialog.png" class="img-fluid">}}

To give other users access to a folder you have created, open that folder and then click its name in the header and select **Members**. Add users or teams who should have access to this folder. Note that any users who have access to the parent folder will automatically have access to this one, but they will not appear in the list.

See [the help site](http://support.crunch.io/articles/ceXXoAEi/Organizing-Datasets-Early-Access) for more information on these features.
