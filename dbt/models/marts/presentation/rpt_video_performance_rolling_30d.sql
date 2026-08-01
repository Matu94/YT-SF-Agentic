{{ config(
    materialized='view'
) }}

SELECT
    v.video_id,
    v.video_title,
    c.channel_title,
    c.organization,
    c.team_studio,
    f.date_id AS metric_date,
    f.rolling_30d_views,
    f.rolling_30d_likes,
    f.rolling_30d_comments
FROM {{ ref('fct_rolling_30d_video_metrics') }} f
JOIN {{ ref('dim_video') }} v ON f.video_id = v.video_id
JOIN {{ ref('dim_channel') }} c ON v.channel_id = c.channel_id
WHERE f.date_id <= DATEADD(day, -1, CURRENT_DATE())
