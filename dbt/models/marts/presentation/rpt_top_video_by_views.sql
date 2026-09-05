{{ config(
    materialized='view'
) }}

WITH latest_metrics AS (
    SELECT *
    FROM (
        SELECT 
            *,
            ROW_NUMBER() OVER(PARTITION BY video_id ORDER BY date_id DESC) as rn
        FROM {{ ref('fct_daily_video_metrics') }}
        WHERE date_id <= DATEADD(day, -1, CURRENT_DATE())
          AND total_views IS NOT NULL
    ) sub
    WHERE rn = 1
)
SELECT
    f.video_id,
    v.video_title,
    v.duration_seconds,
    v.video_type,
    v.published_at,
    v.channel_id,
    d.channel_title,
    d.organization,
    d.team_studio,
    d.content_type,
    f.date_id AS metric_date,
    f.total_views,
    f.total_likes,
    f.total_comments
FROM latest_metrics f
JOIN {{ ref('dim_video') }} v
    ON f.video_id = v.video_id
JOIN {{ ref('dim_channel') }} d
    ON v.channel_id = d.channel_id
    -- SCD Type 2 resolution: map the metric to the correct historical dimension state
    AND f.date_id >= DATE(d.valid_from)
    AND f.date_id < COALESCE(DATE(d.valid_to), '9999-12-31'::DATE)
ORDER BY f.total_views DESC NULLS LAST
LIMIT 50
