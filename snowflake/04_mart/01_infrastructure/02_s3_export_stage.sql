-- ==============================================================
-- 02_s3_export_stage.sql
-- Create the External Stage pointing to AWS S3
-- ==============================================================

CREATE OR REPLACE STAGE MART.S3_EXPORT_STAGE
  URL = 's3://yt-sf-metrics-data-{{SNOWFLAKE_ENVIRONMENT_LOWER}}/mart/'
  STORAGE_INTEGRATION = {{SNOWFLAKE_DATABASE}}_AWS_S3_INTEGRATION
  FILE_FORMAT = (TYPE = PARQUET COMPRESSION = SNAPPY)
  COMMENT = 'External stage for Parquet data exports to AWS S3';
