+++
_schema = "release_note"
date = 2026-06-24T12:33:37.000Z
publishdate = ""
draft = false
title = "Release note 2026.5"
images = [ "https://crunch.io/img/logo-1200x630.png" ]
+++
### **Crunch**

* Search improvements:
  * Updated search to include folders and dashboards. Added new tabs for both Folder search and Dashboard search.
  * Update to make text selectable in search results.
  * Updated the search interface to improve clarity and make keyword search functionality easier to discover.
* Retired legacy and fully transitioned search to a modern vector-based search experience, improving semantic relevance and reducing platform complexity.
* AI Agent improvements:
  * Variables are now links in the agent response and open variables in Explore mode in a new tab.
  * Resolved an issue where the agent incorrectly stated it can perform tasks that are currently out of scope.
* Sharing and collaboration improvements:
  * Shared decks and dashboards now enable users to enter Edit mode to make multiple changes in one session, with a notification explaining that edits will affect all users.
  * Shared artifacts now enforce sharing requirements: personal variables, filters, and analyses cannot be added to shared artifacts, multitables, or decks unless they have been shared first.

### **API endpoints and API reference**

Removed [List datasets in project](https://crunch.io/api/reference/#get-/projects/-project_id-/datasets/) endpoint. This endpoint was replaced with the [List project details](https://crunch.io/api/reference/#get-/projects/-project_id-/) endpoint.

MCP (Beta) - we can now offer a direct connection to the datasets you upload to Crunch via MCP server, connected to your own AI agents and platforms.

### **Lakehouse**

[Lakehouse Tabulation APIs](https://help.crunch.io/hc/en-us/articles/43012931204877-Tabulating-Data-on-the-Lakehouse#toc4) now supports numeric variable type and statistical operations

[Lakehouse Export APIs](https://help.crunch.io/hc/en-us/articles/40974722113293-Exporting-Data-with-Crunch-Lakehouse-APIs#toc7) now support the ability to define variables/folders and inclusive data filters, providing more fine grained control over the data returned

Implemented significant improvements on the [Lakehouse Tabulation APIs](https://help.crunch.io/hc/en-us/articles/43012931204877-Tabulating-Data-on-the-Lakehouse#toc4) when tabulating large volumes of variables

### **Backend/CrunchDB**

Removed alter\_users legacy permission.