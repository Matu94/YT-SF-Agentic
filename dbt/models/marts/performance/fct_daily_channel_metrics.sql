{{ config(
    materialized='table'
) }}

SELECT
    d.channel_sk,
    s.metric_date AS date_id,
    s.total_subscribers,
    s.daily_subscriber_growth,
    s.total_views,
    s.daily_views,
    s.total_videos
FROM {{ ref('stg_youtube_channel_stats') }} s
JOIN {{ ref('dim_channel') }} d
    ON s.channel_id = d.channel_id
    -- SCD Type 2 resolution: map the metric to the correct historical dimension state
    AND s.metric_date >= DATE(d.valid_from)
    AND s.metric_date < COALESCE(DATE(d.valid_to), '9999-12-31'::DATE)
