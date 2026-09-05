# ADR 004: Rolling 7-Day Reporting Layer & Aggregations

## Status
Accepted

## Context
Our current data model successfully tracks daily performance metrics at the video and channel levels via the `fct_daily_video_metrics` and `fct_daily_channel_metrics` models. These are then denormalized into daily OBT (One Big Table) views for Streamlit consumption (`rpt_video_performance_daily` and `rpt_channel_performance_daily`).

There is an emerging need to provide weekly performance overviews and broader trend analysis. However, rather than fixed calendar weeks (e.g., ISO weeks starting on Monday), the requirement is for a **Rolling 7-Day Report**. This means that for any given date, the metrics should represent the aggregate performance of the preceding 7 days.

While Streamlit could dynamically aggregate these rolling metrics on the fly using complex SQL Window Functions (e.g., `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`), doing so upon every user interaction forces the presentation layer to scan and aggregate large daily fact tables. This violates our principle of keeping the Streamlit presentation layer lightweight and can lead to increased Snowflake compute costs and higher dashboard latency.

## Decision
We will extend the Kimball star schema to natively support rolling weekly reporting by introducing pre-aggregated periodic snapshot fact tables and corresponding OBT reporting views.

Specifically, we are adding the following models to our dbt project:

1.  **Rolling 7-Day Fact Tables (Aggregated from Daily Facts via Window Functions):**
    *   `fct_rolling_7d_video_metrics`: Summarizing rolling 7-day performance (`rolling_7d_views`, `rolling_7d_likes`, `rolling_7d_comments`). Grain: 1 row per video per day.
    *   `fct_rolling_7d_channel_metrics`: Summarizing rolling 7-day performance (`rolling_7d_subscriber_growth`, `rolling_7d_views`). Grain: 1 row per channel per day.

2.  **Rolling 7-Day Presentation / Reporting Views (OBT):**
    *   `rpt_video_performance_rolling_7d`: Denormalizes `fct_rolling_7d_video_metrics` with `dim_video` and `dim_channel`.
    *   `rpt_channel_performance_rolling_7d`: Denormalizes `fct_rolling_7d_channel_metrics` with `dim_channel`.

These structures will be managed via dbt. The heavy lifting (calculating the rolling sums over the daily fact tables) will happen once per day in our `YT_SF_TRANSFORM_WH` warehouse during the batch run.

## Consequences
*   **Positive:** Dashboard latency for rolling trend analysis is significantly reduced, offering a snappy user experience. The BI tool simply queries a static row for a given date rather than executing a computationally expensive window function.
*   **Positive:** The Streamlit frontend codebase remains clean; it only executes simple `SELECT` statements.
*   **Positive:** Snowflake compute costs during BI consumption drop. By shifting the window function calculation to our batch transformation layer, we leverage our strict cost controls and prevent unpredictable ad-hoc query costs in the reporting warehouse.
*   **Negative:** Fact table storage increases because we are storing a new row for every video/channel every day in the rolling fact tables. However, Snowflake storage is extremely cheap compared to compute, making this a highly favorable tradeoff.
