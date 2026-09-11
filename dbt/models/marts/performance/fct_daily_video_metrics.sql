{{ config(
    materialized='table'
) }}

SELECT
    video_id,
    metric_date AS date_id,
    total_views,
    daily_views,
    total_likes,
    daily_likes,
    total_comments,
    daily_comments
FROM {{ ref('stg_youtube_video_stats') }}
