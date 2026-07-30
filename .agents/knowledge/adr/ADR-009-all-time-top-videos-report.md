# ADR 009: All-Time Top Videos Reporting Layer

## Status
Proposed

## Context
We have a requirement to build a presentation layer reporting capability to surface the "All-Time Top" performing videos. Specifically, we need to track:
1. The video with the most views.
2. The video with the most likes.
3. The video with the most comments.

The user explicitly requested that these top metrics be maintained in different tables/views to simplify querying and visualization in the Streamlit application.

## Decision
We will extend the Kimball presentation layer by creating three distinct One Big Table (OBT) views. These views will pre-calculate and sort the cumulative performance of all videos up to the current date.

The three new views will be:
*   `rpt_top_video_by_views`
*   `rpt_top_video_by_likes`
*   `rpt_top_video_by_comments`

### Logical Design
These views will be built by querying the latest daily snapshot from `fct_daily_video_metrics` (where the `metric_date` is the maximum available date) and joining it with `dim_video` and `dim_channel`. This ensures all necessary descriptive attributes (channel title, video title, publish date, etc.) are readily available for Streamlit without requiring complex query-time joins. 

We will return the global Top 50 across all channels, ensuring the `channel_title` and `organization` columns are included so it's clear who owns each video. Each view will be sorted in descending order by its respective primary metric (`total_views`, `total_likes`, `total_comments`), without any secondary sort key, and hard-limited using `LIMIT 50` directly in the view definition to optimize compute and data transfer.

## Consequences
*   **Positive:** Streamlit will have direct, zero-join access to the top-performing videos, significantly improving dashboard rendering times and reducing Snowflake compute costs at runtime.
*   **Negative:** Adds three new models to the dbt DAG, slightly increasing the transformation execution time, though the cost will be negligible.
