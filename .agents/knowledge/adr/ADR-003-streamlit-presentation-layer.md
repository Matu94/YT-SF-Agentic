# ADR 003: Streamlit Presentation Layer (One Big Table)

## Status
Accepted

## Context
Our analytical pipeline is built on Snowflake utilizing a Kimball Star Schema design with dimensions (`dim_channel`, `dim_video`, etc.) and fact tables (`fct_daily_channel_metrics`, `fct_daily_video_metrics`). 
While this normalized model is ideal for data warehousing, tracking historical changes (SCD2), and storage efficiency, it poses challenges for our downstream BI consumption tool, Streamlit. 
Streamlit applications execute queries repeatedly upon user interactions. Executing complex multi-way joins between large fact and dimension tables on every interaction leads to higher latency, poorer user experience, and bloated, complex SQL queries embedded within the application codebase. 

## Decision
We will introduce a dedicated **Presentation / Reporting Layer** in the Data Mart that denormalizes the Kimball models into reporting views or One Big Tables (OBTs) specifically optimized for Streamlit consumption. 

Specifically, we are adding two foundational reporting models:
1. `RPT_VIDEO_PERFORMANCE_DAILY`: Denormalizes `fct_daily_video_metrics` with `dim_video` and `dim_channel`.
2. `RPT_CHANNEL_PERFORMANCE_DAILY`: Denormalizes `fct_daily_channel_metrics` with `dim_channel`.

These reporting structures will be managed via dbt and materialized in Snowflake (either as Views or Incremental Tables, depending on performance requirements as data scales).

## Consequences
*   **Positive:** Substantially simplified Streamlit application code. The frontend app only needs to execute simple `SELECT * FROM ... WHERE ...` queries without complex joins.
*   **Positive:** Improved dashboard performance due to pre-computed joins and potentially leveraging Snowflake's optimized columnar storage on denormalized structures.
*   **Negative/Neutral:** Slight increase in storage and compute costs during the dbt transformation phase, as we are creating additional denormalized materializations of the same underlying data. However, this is heavily outweighed by query-time performance gains and app maintainability.
