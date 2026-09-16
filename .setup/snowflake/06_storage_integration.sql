-- ==============================================================
-- 06_storage_integration.sql
-- AWS S3 Storage Integration for Parquet Exports
--
-- PURPOSE:
--   Configures Snowflake's Storage Integration features to allow
--   tasks to export data natively to AWS S3.
--
-- EXECUTION ROLE: YT_SF_PROD_ADMIN_ROLE / YT_SF_DEV_ADMIN_ROLE
--   (Requires CREATE INTEGRATION granted during 02_grant_init.sql)
-- ==============================================================

-- ==============================================================
-- PROD Environment
-- ==============================================================
USE ROLE YT_SF_PROD_ADMIN_ROLE;

CREATE OR REPLACE STORAGE INTEGRATION YT_SF_PROD_AWS_S3_INTEGRATION
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/yt-sf-exporter-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://yt-sf-metrics-data-prod/mart/')
  COMMENT = 'PROD integration granting export access to S3';

GRANT USAGE ON INTEGRATION YT_SF_PROD_AWS_S3_INTEGRATION TO ROLE YT_SF_PROD_TRANSFORM_ROLE;
GRANT USAGE ON INTEGRATION YT_SF_PROD_AWS_S3_INTEGRATION TO ROLE YT_SF_PROD_CICD_ROLE;
GRANT USAGE ON INTEGRATION YT_SF_PROD_AWS_S3_INTEGRATION TO ROLE YT_SF_PROD_LOAD_ROLE;


-- ==============================================================
-- DEV Environment
-- ==============================================================
USE ROLE YT_SF_DEV_ADMIN_ROLE;

CREATE OR REPLACE STORAGE INTEGRATION YT_SF_DEV_AWS_S3_INTEGRATION
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/yt-sf-exporter-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://yt-sf-metrics-data-prod/mart/')
  COMMENT = 'DEV integration granting export access to S3';

GRANT USAGE ON INTEGRATION YT_SF_DEV_AWS_S3_INTEGRATION TO ROLE YT_SF_DEV_TRANSFORM_ROLE;
GRANT USAGE ON INTEGRATION YT_SF_DEV_AWS_S3_INTEGRATION TO ROLE YT_SF_DEV_CICD_ROLE;
GRANT USAGE ON INTEGRATION YT_SF_DEV_AWS_S3_INTEGRATION TO ROLE YT_SF_DEV_LOAD_ROLE;
