# ADR 008: Rolling 30-Day (Monthly) Reporting Layer & Aggregations

## Status
Implemented

## Context
Our current data model tracks daily performance metrics (`fct_daily_video_metrics`, `fct_daily_channel_metrics`) and rolling 7-day weekly metrics (`fct_rolling_7d_video_metrics`, `fct_rolling_7d_channel_metrics`) at the video and channel levels. 

There is an emerging need to provide monthly performance overviews and broader, longer-term trend analysis. Similar to our weekly reporting, rather than using fixed calendar months, the requirement is for a **Rolling 30-Day Report**. This ensures that for any given date, the metrics represent the aggregate performance of the preceding 30 days, providing a smoother and more consistent trend line free from calendar month boundary artifacts.

## Decision
We will extend the Kimball star schema to natively support rolling monthly reporting by introducing new pre-aggregated periodic snapshot fact tables and corresponding OBT (One Big Table) reporting views. This follows the exact same architectural pattern established in ADR-004 for weekly reporting.

Specifically, we require the following additions and modifications to the data platform:

1.  **Create Rolling 30-Day Fact Tables:**
    *   **`fct_rolling_30d_video_metrics`**: Summarizing rolling 30-day performance (`rolling_30d_views`, `rolling_30d_likes`, `rolling_30d_comments`). Grain: 1 row per video per day. Computed via window functions (e.g., `ROWS BETWEEN 29 PRECEDING AND CURRENT ROW`) over `fct_daily_video_metrics`.
    *   **`fct_rolling_30d_channel_metrics`**: Summarizing rolling 30-day performance (`rolling_30d_subscriber_growth`, `rolling_30d_views`). Grain: 1 row per channel per day. Computed via window functions over `fct_daily_channel_metrics`.

2.  **Create Rolling 30-Day Presentation / Reporting Views (OBT):**
    *   **`rpt_video_performance_rolling_30d`**: Denormalizes `fct_rolling_30d_video_metrics` by joining with `dim_video` and `dim_channel` to serve the presentation layer without query-time joins.
    *   **`rpt_channel_performance_rolling_30d`**: Denormalizes `fct_rolling_30d_channel_metrics` by joining with `dim_channel`.

3.  **Modify Existing Documentation:**
    *   Update the logical data model documentation (`.agents/rules/02-data-model.md`), including the ERD, Table Definitions, and Source-to-Target Mappings, to reflect these new entities and their relationships.

These new models will be orchestrated via dbt. The heavy lifting of calculating rolling sums over daily fact tables will execute once per day in our designated transformation warehouse (`YT_SF_TRANSFORM_WH`) during the batch run.

## Consequences
*   **Positive:** Adheres to established architectural patterns, keeping the presentation layer logic clean, fast, and thin.
*   **Positive:** Shifting complex window function calculations to the batch transformation layer prevents unpredictable ad-hoc query costs in the reporting warehouse.
*   **Positive:** Downstream BI tools will query a static row for a given date rather than executing computationally expensive aggregations on the fly.
*   **Negative:** Adds to our total fact table storage footprint by requiring a new row for every video/channel every day in the new rolling tables. However, Snowflake storage is extremely cheap compared to compute, making this a highly favorable tradeoff.
