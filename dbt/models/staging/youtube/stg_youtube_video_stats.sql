{{ config(
    materialized='incremental',
    unique_key=['video_id', 'metric_date'],
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
) }}

WITH raw_data AS (
    SELECT
        video_id,
        channel_id,
        video_title,
        published_at,
        duration_iso8601,
        live_broadcast_content,
        total_views,
        total_likes,
        total_comments,
        CAST(extracted_at AS DATE) AS metric_date,
        extracted_at
    FROM {{ source('raw_youtube', 'v_youtube_parsed_videos') }}
    
    {% if is_incremental() %}
    -- Select new data plus the most recent existing day to enable LAG calculations
    WHERE CAST(extracted_at AS DATE) >= (
        SELECT COALESCE(max(metric_date), '1970-01-01'::DATE) FROM {{ this }}
    )
    {% endif %}
),

deduplicated_raw AS (
    SELECT
        video_id,
        channel_id,
        video_title,
        published_at,
        duration_iso8601,
        live_broadcast_content,
        total_views,
        total_likes,
        total_comments,
        metric_date
    FROM (
        SELECT
            video_id,
            channel_id,
            video_title,
            published_at,
            duration_iso8601,
            live_broadcast_content,
            total_views,
            total_likes,
            total_comments,
            metric_date,
            ROW_NUMBER() OVER (
                PARTITION BY video_id, metric_date
                ORDER BY extracted_at DESC
            ) AS rn
        FROM raw_data
    )
    WHERE rn = 1
),

calculated_metrics AS (
    SELECT
        video_id,
        channel_id,
        video_title,
        published_at,
        duration_iso8601,
        live_broadcast_content,
        total_views,
        total_likes,
        total_comments,
        metric_date,
        
        -- Calculate daily growth metrics using LAG over the video's history
        total_views - LAG(total_views, 1) OVER (
            PARTITION BY video_id 
            ORDER BY metric_date ASC
        ) AS daily_views,
        
        total_likes - LAG(total_likes, 1) OVER (
            PARTITION BY video_id 
            ORDER BY metric_date ASC
        ) AS daily_likes,
        
        total_comments - LAG(total_comments, 1) OVER (
            PARTITION BY video_id 
            ORDER BY metric_date ASC
        ) AS daily_comments

    FROM deduplicated_raw
)

SELECT *
FROM calculated_metrics
{% if is_incremental() %}
-- Only merge the truly new rows into the target table
WHERE metric_date > (SELECT COALESCE(max(metric_date), '1970-01-01'::DATE) FROM {{ this }})
{% endif %}
