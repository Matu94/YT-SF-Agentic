# ADR-002: Video Metrics Pipeline Architecture & Delta Engine

## Status
Accepted

## Context
As part of the continuous expansion of the YouTube Metrics Pipeline, we need to ingest and track detailed daily video-level data (views, likes, comments, duration, title) for various Hungarian channels.

This requires:
1. Validating that the ingestion flow aligns with Kimball modeling principles.
2. Designing logical schema mappings for the Staging and Mart layers.
3. Defining a SQL-safe Snowflake transformation to parse ISO 8601 duration strings (e.g., `'PT1H23M45S'`) into `duration_seconds`.
4. Designing a scalable, performant strategy for daily delta window calculations (`LAG`) over large, historical video datasets.

---

## Decision

### 1. Ingestion Flow Review (Kimball Alignment)

We approve the proposed ingestion flow:
```text
[YouTube Data API]
       │
       ▼ (Snowpark Stored Procedure)
[LANDING.YOUTUBE_RAW_DATA] (Transient, raw JSON drop)
       │
       ▼ (Incremental MERGE/INSERT)
[RAW.YOUTUBE_RAW_DATA]     (Persistent, raw JSON history)
       │
       ▼ (dbt Staging View / Table)
[STAGING.STG_YOUTUBE_VIDEO_STATS] / [STAGING.STG_YOUTUBE_CHANNEL_STATS]
       │
       ▼ (dbt Mart Materialization)
[MART.DIM_VIDEO] / [MART.FCT_DAILY_VIDEO_METRICS]
```

**Kimball Alignment Principles:**
- **Raw Storage:** `RAW.YOUTUBE_RAW_DATA` stores the unmodified, exact JSON response from the YouTube API. This ensures we can rebuild downstream tables at any time.
- **Grain Isolation:** The raw table stores heterogeneous payloads (channel stats and video stats) in a single variant table. The Staging layer is responsible for separating these payloads and establishing the correct grain:
  - **Channel stats grain:** One row per channel, per day (`stg_youtube_channel_stats`).
  - **Video stats grain:** One row per video, per day (`stg_youtube_video_stats`).
- **Separation of Concerns:** Staging flattens the JSON, casts data types, parses durations, and calculates daily deltas. Marts house the star schema dimensions and fact tables, joining the staging data against organizational seeds (e.g., `SEED_CHANNELS_HIERARCHY`).

---

### 2. Logical Schema Mappings

#### A. Staging Layer

##### `stg_youtube_channel_stats`
- **Source:** `RAW.YOUTUBE_RAW_DATA` (Filtered where `RAW_JSON:kind::string = 'youtube#channelListResponse'`)
- **JSON Flattening:** `LATERAL FLATTEN(input => RAW_JSON:items)`

| Column Name | Data Type | Source Path / Formula | Constraints / Description |
| :--- | :--- | :--- | :--- |
| `channel_id` | `VARCHAR` | `item.value:id::varchar` | PK, Natural Key |
| `metric_date` | `DATE` | `extracted_at::date` | PK, date of extraction |
| `channel_title` | `VARCHAR` | `item.value:snippet.title::varchar` | SCD Type 2 attribute |
| `channel_custom_url` | `VARCHAR` | `item.value:snippet.customUrl::varchar` | SCD Type 2 attribute |
| `channel_published_at` | `TIMESTAMP_TZ` | `item.value:snippet.publishedAt::timestamp_tz` | Static metadata |
| `channel_country` | `VARCHAR` | `item.value:snippet.country::varchar` | Country code |
| `total_subscribers` | `INTEGER` | `item.value:statistics.subscriberCount::integer` | Cumulative count (>= 0) |
| `total_views` | `INTEGER` | `item.value:statistics.viewCount::integer` | Cumulative count (>= 0) |
| `total_videos` | `INTEGER` | `item.value:statistics.videoCount::integer` | Cumulative count (>= 0) |
| `daily_subscriber_growth` | `INTEGER` | `total_subscribers - LAG(total_subscribers) OVER (PARTITION BY channel_id ORDER BY metric_date)` | Daily growth calculation |
| `extracted_at` | `TIMESTAMP_TZ` | `extracted_at` | Ingestion audit timestamp |

##### `stg_youtube_video_stats`
- **Source:** `RAW.YOUTUBE_RAW_DATA` (Filtered where `RAW_JSON:kind::string = 'youtube#videoListResponse'`)
- **JSON Flattening:** `LATERAL FLATTEN(input => RAW_JSON:items)`

| Column Name | Data Type | Source Path / Formula | Constraints / Description |
| :--- | :--- | :--- | :--- |
| `video_id` | `VARCHAR` | `item.value:id::varchar` | PK, Natural Key |
| `channel_id` | `VARCHAR` | `item.value:snippet.channelId::varchar` | FK to channel |
| `metric_date` | `DATE` | `extracted_at::date` | PK, date of extraction |
| `video_title` | `VARCHAR` | `item.value:snippet.title::varchar` | Static metadata |
| `duration_raw` | `VARCHAR` | `item.value:contentDetails.duration::varchar` | Raw ISO 8601 duration string |
| `duration_seconds` | `INTEGER` | *ISO 8601 Regex Parser Formula* | Parsed duration in seconds |
| `published_at` | `TIMESTAMP_TZ` | `item.value:snippet.publishedAt::timestamp_tz` | Static publish timestamp |
| `total_views` | `INTEGER` | `item.value:statistics.viewCount::integer` | Cumulative count (>= 0) |
| `total_likes` | `INTEGER` | `COALESCE(item.value:statistics.likeCount::integer, 0)` | Cumulative count (>= 0) |
| `total_comments` | `INTEGER` | `COALESCE(item.value:statistics.commentCount::integer, 0)` | Cumulative count (>= 0) |
| `extracted_at` | `TIMESTAMP_TZ` | `extracted_at` | Ingestion audit timestamp |

#### B. Mart Layer

##### `dim_video`
- **Source:** `STAGING.STG_YOUTUBE_VIDEO_STATS` (Deduplicated, taking earliest record per `video_id`)
- **Grain:** One row per unique video. Contains static descriptors.

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `video_id` | `VARCHAR` | PK |
| `channel_id` | `VARCHAR` | FK to `dim_channel` |
| `video_title` | `VARCHAR` | Title of the video |
| `duration_seconds` | `INTEGER` | Video length in seconds |
| `published_at` | `TIMESTAMP_TZ` | Publish timestamp |

##### `fct_daily_video_metrics`
- **Source:** `STAGING.STG_YOUTUBE_VIDEO_STATS`
- **Grain:** One row per video, per day.

| Column Name | Data Type | Source Path / Formula |
| :--- | :--- | :--- |
| `video_sk` | `VARCHAR` | `MD5(video_id || '|' || date_id)` or composite PK |
| `video_id` | `VARCHAR` | FK to `dim_video` |
| `date_id` | `DATE` | FK to `dim_date` (metric date) |
| `total_views` | `INTEGER` | Cumulative views at end of day |
| `daily_views` | `INTEGER` | *Delta Calculation with Spike Handling* |
| `total_likes` | `INTEGER` | Cumulative likes at end of day |
| `daily_likes` | `INTEGER` | *Delta Calculation with Spike Handling* |
| `total_comments` | `INTEGER` | Cumulative comments at end of day |
| `daily_comments` | `INTEGER` | *Delta Calculation with Spike Handling* |

---

### 3. ISO 8601 Duration Parser

We define a SQL-safe Snowflake expression to extract days, hours, minutes, and seconds from the ISO 8601 duration format (e.g., `'PT1H23M45S'`, `'PT15M'`, `'P1D'`) using `REGEXP_SUBSTR` and `TRY_TO_NUMBER`.

```sql
COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(duration_raw, '(\\d+)D', 1, 1, 'e', 1)), 0) * 86400 +
COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(duration_raw, '(\\d+)H', 1, 1, 'e', 1)), 0) * 3600 +
COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(duration_raw, '(\\d+)M', 1, 1, 'e', 1)), 0) * 60 +
COALESCE(TRY_TO_NUMBER(REGEXP_SUBSTR(duration_raw, '(\\d+)S', 1, 1, 'e', 1)), 0)
```

**Why this is SQL-safe:**
- `REGEXP_SUBSTR(..., 'e', 1)` extracts the numeric string inside the capture group (e.g. `'23'` from `'23M'`).
- `TRY_TO_NUMBER` safely converts the string to an integer, returning `NULL` instead of throwing an error if the string is malformed.
- `COALESCE(..., 0)` defaults missing components (like `H` in `PT15M` or `D` in `PT1H`) to `0`.
- The parsed units are multiplied by their respective seconds conversions (86400 for Days, 3600 for Hours, 60 for Minutes, 1 for Seconds) and summed.

---

### 4. Daily Delta Calculations & Performance Considerations

#### A. Initial Onboarding Spike Handling
When calculating daily deltas (`Today - Yesterday`), a major problem is the "Onboarding Spike": the first time a video is tracked, there is no "yesterday" record. A simple `COALESCE(total_views - LAG(total_views), total_views)` would record the video's entire lifetime views as the daily views for the first tracking day.

To solve this, we check if the tracking date matches the video's published date:
```sql
CASE
    -- Scenario 1: We have history, compute standard delta
    WHEN LAG(total_views) OVER (PARTITION BY video_id ORDER BY metric_date) IS NOT NULL
        THEN total_views - LAG(total_views) OVER (PARTITION BY video_id ORDER BY metric_date)
    
    -- Scenario 2: First day tracked, and the video was published today
    WHEN metric_date = published_at::date
        THEN total_views
        
    -- Scenario 3: First day tracked, but the video is older (backfill/onboarded historical video)
    ELSE 0
END AS daily_views
```
*(This applies identically to `daily_likes` and `daily_comments`.)*

#### B. Scale and Performance Optimizations for Window Functions (`LAG`)
As the pipeline expands to track thousands of videos daily, running `LAG` window functions over the entire history of `RAW` data will lead to performance degradation. We implement the following strategies:

1. **Incremental Materialization in dbt:**
   Rather than performing a full table rebuild each run, `fct_daily_video_metrics` should use `incremental` materialization.
   During incremental runs:
   - Filter `stg_youtube_video_stats` to only include new raw data.
   - For each video, join the new record against the *latest record in the existing fact table* to serve as the "yesterday" baseline.
   - This localizes the delta calculation to $O(N)$ where $N$ is only the daily new records, rather than running a window function over all historical rows ($O(M)$ where $M$ is total historical records).

2. **Snowflake Clustering Keys:**
   - Cluster the `RAW.YOUTUBE_RAW_DATA` table by `(EXTRACTED_AT::DATE)` or `(RAW_JSON:kind::string, EXTRACTED_AT::DATE)`. This ensures that dbt incremental runs prune partitions and only read the specific daily API payloads.
   - Cluster `MART.FCT_DAILY_VIDEO_METRICS` by `(DATE_ID, VIDEO_ID)`. This optimizes time-series queries for Streamlit (which usually filter on recent dates).

3. **Data Type Optimizations:**
   - Store all natural keys (`video_id`, `channel_id`) as `VARCHAR` and date/timestamp fields as native `DATE` and `TIMESTAMP_TZ` (not strings). This ensures high-performance joins and compact storage.

---

## Consequences

- **Positive:**
  - Robust delta calculations that eliminate artificial view/like/comment spikes on video onboarding.
  - A clean, performant incremental dbt design that scales seamlessly as more channels are continuously added.
  - Native, SQL-safe duration parsing using built-in Snowflake regex functions without requiring external libraries or UDF deployment overhead.
- **Negative:**
  - Window functions (`LAG`) in the initial backfill run will still require full table scans, but this is a one-time operation.
  - Incremental logic in dbt must be carefully tested to ensure it handles late-arriving data correctly (by looking back a few days if needed).
