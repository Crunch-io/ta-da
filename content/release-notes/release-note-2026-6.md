+++
_schema = "release_note"
date = 2026-08-10T14:32:15.601Z
publishdate = ""
draft = false
title = "Release note 2026.6"
images = [ "https://crunch.io/img/logo-1200x630.png" ]
+++
### **Crunch**

AI Agent improvements:

* Added low base size warning message for Multiple Response and Categorical Array variables in the AI Agent.
* Strengthened accuracy when reading and ranking values from larger or more complex tables created in the AI Agent.
* Improved validation of user-supplied input against real data.
* Added cleaner instructions and limitations when working with dates.

Search improvements:

* Updated folder search results for in-dataset search to be displayed alphabetically.
* Added tool-tip to show variable question for Best Match in-dataset search results.
* Increased the minimum search threshold to decrease the number of less relevant search results.

Collaboration and sharing:

* Implemented promotion of nested artifacts for all artifact types: when users share an artifact, all its personal dependencies (nested artifacts) become shared as well.
* Updated the sharing UI: sharing action is now clearly separated from editing; sharing is enabled after any changes have been saved.
* Consistent access level: when an artifact of any type is created, it defaults to personal. Decks and dashboards can be shared at the point of creation, variables, filters and multitables can be shared after they’ve been saved.
* Flexibility in dashboards: personal artifacts can now be used in personal dashboards. If the dashboard is then shared, the nested personal artifacts get promoted to shared.

Updated breadcrumbs to be responsive for users with small screen resolutions.