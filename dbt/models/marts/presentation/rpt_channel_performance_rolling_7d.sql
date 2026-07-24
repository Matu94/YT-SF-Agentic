{{ config(
    materialized='view'
) }}

SELECT
    c.channel_id,
    c.channel_title,
    c.organization,
    c.team_studio,
    f.date_id AS metric_date,
    f.rolling_7d_subscriber_growth,
    f.rolling_7d_views
FROM {{ ref('fct_rolling_7d_channel_metrics') }} f
JOIN {{ ref('dim_channel') }} c ON f.channel_sk = c.channel_sk
