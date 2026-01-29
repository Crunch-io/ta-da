+++
_schema = "feature_yaml"
date = 2026-01-29T11:52:22.869Z
publishdate = ""
draft = false
title = "Tabulation API"
description = "Turn survey data into pipeline-ready intelligence. The Tabulation API delivers aggregated cross-tabs directly to your warehouses and dashboards."
news_description = "The Tabulation API provides a programmatic way to work with aggregated data directly, removing the need to process respondent-level data. Built for teams that need survey insights on their terms, this API feeds cross-tabulations directly into your dashboards, data warehouses, and reporting workflows."
weight = 20
tags = [ "" ]
categories = [ "feature" ]
images = [ "https://crunch.io/img/logo-1200x630.png" ]
labs_only = false
no_profiles = false
no_yougov = false
+++
The Tabulation API provides a programmatic way to work with aggregated data directly, removing the need to process respondent-level data. Built for teams that need survey insights on their terms, this API feeds cross-tabulations directly into your dashboards, data warehouses, and reporting workflows.

## What is the Tabulation API?

The Tabulation API is a flexible export interface for aggregated survey data, providing:

* **Asynchronous batch cross-tabulations** with any combination of row and column variables.
* **Row-level filtering** using a declarative syntax.
* **Long-form output** designed for ingestion into reporting pipelines.

## Use Cases

* **Ingest Aggregated Intelligence:** Feed your DataLakes (e.g., Snowflake, BigQuery) with aggregated cross-tabulations. This allows you to store lightweight, statistical summaries that represent millions of data points, ready for historical tracking or modeling.
* **Supercharge Internal Dashboards:** Inject YouGov's data directly into your proprietary BI tools (Tableau, PowerBI, Looker). By visualizing comparison metrics alongside your internal sales or churn data, you create a unified view of the customer.
* **Automated Trend Snapshots:** Set up monthly automated jobs to capture how an audience evolves. Track specific segments (e.g., “Early Adopters”) over time to see if their affinity for your brand (index) or their distinctiveness (z-score) is growing or shrinking.

## Outputs

Results are delivered as long-form CSV, with one row per cell of the tabulation matrix. This format:

* Loads directly into SQL databases and warehouses without pivoting.
* Works natively with pandas, R data frames, and BI tools.
* Scales cleanly as you add row or column variables.

Each row contains identifiers for the **row variable, column variables, counts, and proportions**.

&nbsp;

Read the full developer guide with examples: [https://help.crunch.io/hc/en-us/articles/43012931204877-Tabulating-Data-on-the-Lakehouse]()

Read the full API reference here \[TODO\]

&nbsp;