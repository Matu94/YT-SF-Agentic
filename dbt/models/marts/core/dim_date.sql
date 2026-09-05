{{ config(
    materialized='view'
) }}

WITH date_spine AS (
    SELECT 
        DATEADD(day, ROW_NUMBER() OVER(ORDER BY NULL) - 1, '2015-01-01'::DATE) AS date_id
    FROM TABLE(GENERATOR(rowcount => 10000))
)

SELECT
    date_id,
    EXTRACT(YEAR FROM date_id) AS year,
    EXTRACT(MONTH FROM date_id) AS month,
    EXTRACT(DAY FROM date_id) AS day,
    DAYNAME(date_id) AS day_of_week
FROM date_spine
