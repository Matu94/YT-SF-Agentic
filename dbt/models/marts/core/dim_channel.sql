{{ config(
    materialized='view'
) }}

SELECT
    dbt_scd_id AS channel_sk,
    channel_id,
    channel_title,
    channel_custom_url,
    channel_country,
    channel_published_at,
    organization,
    team_studio,
    content_type,
    -- Back-extend the first version of the dimension to handle historical facts
    CASE 
        WHEN ROW_NUMBER() OVER (PARTITION BY channel_id ORDER BY dbt_valid_from) = 1 
        THEN '1970-01-01'::TIMESTAMP_NTZ 
        ELSE dbt_valid_from 
    END AS valid_from,
    dbt_valid_to AS valid_to,
    CASE 
        WHEN dbt_valid_to IS NULL THEN TRUE 
        ELSE FALSE 
    END AS is_active
FROM {{ ref('dim_channel_snapshot') }}
