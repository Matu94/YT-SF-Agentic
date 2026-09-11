# ADR-006: Metric Date Bounding to Published Date

## 1. Context & Problem Statement
The YouTube Metrics Pipeline extracts data in the early morning (e.g., 04:00 AM) to capture the previous day's performance. To accurately reflect this in the dimensional layer, the pipeline shifts the extraction date by -1 day:
```sql
DATEADD(day, -1, CAST(extracted_at AS DATE)) AS metric_date
```

**The Logical Flaw:**
If an extraction occurs on the *same day* a video is published (e.g., due to a manual ad-hoc run, or an intra-day schedule change), the `-1 day` shift forces the `metric_date` to be the day *before* the video was officially published. 
For example:
*   Video Published: `2026-07-25 10:00:00`
*   Ad-hoc Pipeline Run: `2026-07-25 14:00:00`
*   Resulting `metric_date`: `2026-07-24`

When the normal scheduled pipeline runs the next morning (`2026-07-26 04:00:00`), it generates a new record for `metric_date = 2026-07-25`. 
Because a prior record exists for `2026-07-24`, the `LAG()` function in `stg_youtube_video_stats.sql` evaluates successfully. Consequently, on the actual published date (`2026-07-25`), the `daily_views` calculation subtracts the views accumulated on the 24th from the lifetime total, resulting in:
**Period Views != Lifetime Views on the Published Date.**

## 2. Decision & Recommendations

To guarantee that metrics are never attributed to a date prior to a video's publication, we must enforce a lower bound on the `metric_date` computation. 

### Action Items for the User (Source Code Modifications):

1.  **Implement the GREATEST() Bound in Staging Models:**
    Update `stg_youtube_video_stats.sql` to ensure `metric_date` is never earlier than the video's local published date.
    
    *Current Implementation:*
    ```sql
    DATEADD(day, -1, CAST(extracted_at AS DATE)) AS metric_date
    ```
    
    *Recommended Implementation:*
    ```sql
    GREATEST(
        DATEADD(day, -1, CAST(extracted_at AS DATE)), 
        CAST(CONVERT_TIMEZONE('UTC', 'Europe/Budapest', published_at) AS DATE)
    ) AS metric_date
    ```
    *(Note: We also recommend converting the `published_at` UTC timestamp to the local timezone to ensure exact calendar alignment).*

2.  **Apply to Channel Staging (Optional but Recommended):**
    For consistency, the same bounding logic can be applied to `stg_youtube_channel_stats.sql` using the channel's `published_at` timestamp.

## 3. Consequences
*   **Pros:** 
    *   Eliminates the "metrics before published" logical anomaly.
    *   If multiple intra-day extractions happen on the published date, they will correctly map to the published date, and the existing `ROW_NUMBER() OVER (...)` deduplication logic will safely keep only the latest extraction.
    *   `daily_views` will correctly equal `total_views` on the day of publication since no prior-day `LAG` record will exist.
*   **Cons:** 
    *   Requires a full refresh (`--full-refresh`) of the staging and fact tables for historical data to recalculate the bounds properly.

*As the Principal Data Architect, I advise making this change to the foundational staging layer to ensure logical integrity downstream.*
