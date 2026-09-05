{% snapshot dim_channel_snapshot %}

{{
    config(
      target_schema='mart',
      unique_key='channel_id',
      strategy='check',
      check_cols=['channel_title', 'channel_custom_url', 'channel_country', 'organization', 'team_studio', 'content_type']
    )
}}

-- We take the most recent record per channel from staging to compare against the snapshot
WITH latest_staging AS (
    SELECT 
        channel_id,
        channel_title,
        channel_custom_url,
        channel_country,
        channel_published_at
    FROM {{ ref('stg_youtube_channel_stats') }}
    -- Qualify ensures we only snapshot the latest state for each run
    QUALIFY ROW_NUMBER() OVER (PARTITION BY channel_id ORDER BY metric_date DESC) = 1
)

SELECT
    s.channel_id,
    s.channel_title,
    s.channel_custom_url,
    s.channel_country,
    s.channel_published_at,
    h.organization,
    h.team_studio,
    h.content_type
FROM latest_staging s
LEFT JOIN {{ ref('channels_hierarchy') }} h
    ON s.channel_id = h.channel_id

{% endsnapshot %}
