{{ config(
    materialized='view'
) }}

WITH raw_videos AS (
    SELECT DISTINCT
        video_id,
        channel_id,
        video_title,
        published_at,
        duration_iso8601,
        live_broadcast_content
    FROM {{ ref('stg_youtube_video_stats') }}
),

parsed_durations AS (
    SELECT
        video_id,
        channel_id,
        video_title,
        published_at,
        duration_iso8601,
        live_broadcast_content,
        -- 'e' flag allows extraction of the first matching group
        TRY_CAST(REGEXP_SUBSTR(duration_iso8601, '([0-9]+)H', 1, 1, 'e', 1) AS INT) AS hours,
        TRY_CAST(REGEXP_SUBSTR(duration_iso8601, '([0-9]+)M', 1, 1, 'e', 1) AS INT) AS minutes,
        TRY_CAST(REGEXP_SUBSTR(duration_iso8601, '([0-9]+)S', 1, 1, 'e', 1) AS INT) AS seconds
    FROM raw_videos
),

calculated_duration AS (
    SELECT
        video_id,
        channel_id,
        video_title,
        published_at,
        live_broadcast_content,
        COALESCE(hours, 0) * 3600 + COALESCE(minutes, 0) * 60 + COALESCE(seconds, 0) AS duration_seconds
    FROM parsed_durations
)

SELECT
    video_id,
    channel_id,
    video_title,
    published_at,
    duration_seconds,
    CASE 
        WHEN duration_seconds <= 60 OR LOWER(video_title) LIKE '%#shorts%' THEN 'short'
        WHEN live_broadcast_content IN ('live', 'upcoming') THEN 'live'
        ELSE 'video'
    END AS video_type
FROM calculated_duration
