{{ config(
    materialized='table'
) }}

SELECT
    video_id,
    date_id,
    SUM(daily_views) OVER (
        PARTITION BY video_id 
        ORDER BY date_id 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_views,
    SUM(daily_likes) OVER (
        PARTITION BY video_id 
        ORDER BY date_id 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_likes,
    SUM(daily_comments) OVER (
        PARTITION BY video_id 
        ORDER BY date_id 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_comments
FROM {{ ref('fct_daily_video_metrics') }}
