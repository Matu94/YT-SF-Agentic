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
    f.rolling_7d_views,
    f.rolling_7d_likes,
    f.rolling_7d_comments
FROM {{ ref('fct_rolling_7d_video_metrics') }} f
JOIN {{ ref('dim_video') }} v ON f.video_id = v.video_id
JOIN {{ ref('dim_channel') }} c 
    ON v.channel_id = c.channel_id
    AND f.date_id >= DATE(c.valid_from)
    AND f.date_id < COALESCE(DATE(c.valid_to), '9999-12-31'::DATE)
WHERE f.date_id <= DATEADD(day, -1, CURRENT_DATE())
