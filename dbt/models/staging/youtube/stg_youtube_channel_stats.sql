{{ config(
    materialized='incremental',
    unique_key=['channel_id', 'metric_date'],
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
) }}

WITH raw_data AS (
    SELECT
        channel_id,
        channel_title,
        channel_custom_url,
        channel_published_at,
        channel_country,
        total_subscribers,
        total_views,
        total_videos,
        GREATEST(
            DATEADD(day, -1, CAST(extracted_at AS DATE)), 
            CAST(CONVERT_TIMEZONE('Europe/Budapest', channel_published_at) AS DATE)
        ) AS metric_date,
        extracted_at
    FROM {{ source('raw_youtube', 'v_youtube_parsed_channels') }}
    
    {% if is_incremental() %}
    -- Select new data plus a 3-day history buffer to enable LAG calculations for the lookback window
    WHERE GREATEST(
        DATEADD(day, -1, CAST(extracted_at AS DATE)), 
        CAST(CONVERT_TIMEZONE('Europe/Budapest', channel_published_at) AS DATE)
    ) >= (
        SELECT DATEADD(day, -3, COALESCE(max(metric_date), '1970-01-01'::DATE)) FROM {{ this }}
    )
    {% endif %}
),

deduplicated_raw AS (
    SELECT
        channel_id,
        channel_title,
        channel_custom_url,
        channel_published_at,
        channel_country,
        total_subscribers,
        total_views,
        total_videos,
        metric_date
    FROM (
        SELECT
            channel_id,
            channel_title,
            channel_custom_url,
            channel_published_at,
            channel_country,
            total_subscribers,
            total_views,
            total_videos,
            metric_date,
            ROW_NUMBER() OVER (
                PARTITION BY channel_id, metric_date
                ORDER BY extracted_at DESC
            ) AS rn
        FROM raw_data
    )
    WHERE rn = 1
),

calculated_metrics AS (
    SELECT
        channel_id,
        channel_title,
        channel_custom_url,
        channel_published_at,
        channel_country,
        total_subscribers,
        total_views,
        total_videos,
        metric_date,
        -- Calculate daily growth using LAG over the channel's history
        COALESCE(
            total_subscribers - LAG(total_subscribers, 1) OVER (
                PARTITION BY channel_id 
                ORDER BY metric_date ASC
            ),
            CASE 
                WHEN CAST(channel_published_at AS DATE) >= DATEADD(day, -3, metric_date) THEN total_subscribers
                ELSE 0
            END
        ) AS daily_subscriber_growth,
        -- Calculate daily views
        COALESCE(
            total_views - LAG(total_views, 1) OVER (
                PARTITION BY channel_id 
                ORDER BY metric_date ASC
            ),
            CASE 
                WHEN CAST(channel_published_at AS DATE) >= DATEADD(day, -3, metric_date) THEN total_views
                ELSE 0
            END
        ) AS daily_views
    FROM deduplicated_raw
)

SELECT *
FROM calculated_metrics
{% if is_incremental() %}
-- 2-day lookback window: re-merge recent days to ensure newly published channels haven't artificially pushed the high-water mark past yesterday's metrics
WHERE metric_date > (SELECT DATEADD(day, -2, COALESCE(max(metric_date), '1970-01-01'::DATE)) FROM {{ this }})
{% endif %}
