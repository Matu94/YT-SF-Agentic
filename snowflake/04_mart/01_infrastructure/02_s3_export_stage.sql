-- ==============================================================
-- 02_s3_export_stage.sql
-- Create the External Stage pointing to AWS S3
-- ==============================================================

USE ROLE {{SNOWFLAKE_DATABASE}}_TRANSFORM_ROLE;
USE DATABASE {{SNOWFLAKE_DATABASE}};
USE SCHEMA MART;

CREATE OR REPLACE STAGE S3_EXPORT_STAGE
  URL = 's3://yt-sf-metrics-data-prod/mart/{{SNOWFLAKE_ENVIRONMENT}}/'
  STORAGE_INTEGRATION = YT_SF_{{SNOWFLAKE_ENVIRONMENT}}_AWS_S3_INTEGRATION
  FILE_FORMAT = (TYPE = PARQUET COMPRESSION = SNAPPY)
  COMMENT = 'External stage for Parquet data exports to AWS S3';
