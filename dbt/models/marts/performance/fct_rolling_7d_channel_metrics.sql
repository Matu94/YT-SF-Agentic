{{ config(
    materialized='table'
) }}

SELECT
    channel_sk,
    date_id,
    SUM(daily_subscriber_growth) OVER (
        PARTITION BY channel_sk 
        ORDER BY date_id 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7d_subscriber_growth,
    SUM(daily_views) OVER (
        PARTITION BY channel_sk 
        ORDER BY date_id 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7d_views
FROM {{ ref('fct_daily_channel_metrics') }}
