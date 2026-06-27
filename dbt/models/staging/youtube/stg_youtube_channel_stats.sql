{{ config(
    materialized='incremental',
    unique_key=['channel_id', 'metric_date'],
    incremental_strategy='merge'
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
        CAST(extracted_at AS DATE) AS metric_date
    FROM {{ source('raw_youtube', 'v_youtube_parsed_channels') }}
    
    {% if is_incremental() %}
    -- Select new data plus the most recent existing day to enable LAG calculations
    WHERE CAST(extracted_at AS DATE) >= (
        SELECT COALESCE(max(metric_date), '1970-01-01'::DATE) FROM {{ this }}
    )
    {% endif %}
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
        total_subscribers - LAG(total_subscribers, 1) OVER (
            PARTITION BY channel_id 
            ORDER BY metric_date ASC
        ) AS daily_subscriber_growth
    FROM raw_data
)

SELECT *
FROM calculated_metrics
{% if is_incremental() %}
-- Only merge the truly new rows into the target table
WHERE metric_date > (SELECT COALESCE(max(metric_date), '1970-01-01'::DATE) FROM {{ this }})
{% endif %}
