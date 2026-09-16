-- ==============================================================
-- 01_export_parquet_task.sql
-- Task to schedule the daily export of Parquet files to S3
-- ==============================================================
CREATE OR REPLACE TASK MART.EXPORT_MART_TO_S3_TASK
  WAREHOUSE = YT_SF_TRANSFORM_WH
  SCHEDULE = 'USING CRON 30 2 * * * Europe/Budapest'
  COMMENT = 'Daily task to export presentation views to S3 as Parquet'
AS
  CALL EXPORT_MART_TO_S3();

-- The task is created suspended by default. 
-- In a real environment, you would enable it via:
-- ALTER TASK EXPORT_MART_TO_S3_TASK RESUME;
