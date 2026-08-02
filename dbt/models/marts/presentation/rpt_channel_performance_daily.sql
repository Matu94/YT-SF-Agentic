{{ config(
    materialized='view'
) }}

SELECT
    d.channel_id,
    d.channel_title,
    d.organization,
    d.team_studio,
    d.content_type,
    f.date_id AS metric_date,
    f.total_subscribers,
    f.daily_subscriber_growth,
    f.total_views,
    f.daily_views,
    f.total_videos
FROM {{ ref('fct_daily_channel_metrics') }} f
JOIN {{ ref('dim_channel') }} d
    ON f.channel_sk = d.channel_sk
WHERE f.date_id <= DATEADD(day, -1, CURRENT_DATE())
