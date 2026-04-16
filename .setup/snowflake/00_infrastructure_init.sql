USE ROLE SYSADMIN;

-- 1. Create the database
CREATE DATABASE IF NOT EXISTS YT_SF_PROD
  COMMENT = 'Production database for YouTube Metrics pipeline';

-- 2. Create Warehouses
CREATE WAREHOUSE IF NOT EXISTS YT_SF_CICD_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  COMMENT = 'Warehouse for CI/CD ingestion and deployment';

CREATE WAREHOUSE IF NOT EXISTS YT_SF_TRANSFORM_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  COMMENT = 'Warehouse for transformation, dbt, and manual queries';

-- 3. Create Managed Access Schemas
-- Creating WITH MANAGED ACCESS ensures that whoever owns the schema centrally manages permissions
-- rather than the object creator retaining individual object ownership.
CREATE SCHEMA IF NOT EXISTS YT_SF_PROD.LANDING WITH MANAGED ACCESS
  COMMENT = 'Transient landing area for raw data extracts';

CREATE SCHEMA IF NOT EXISTS YT_SF_PROD.RAW WITH MANAGED ACCESS
  COMMENT = 'Persistent historical storage layer';

CREATE SCHEMA IF NOT EXISTS YT_SF_PROD.STAGING WITH MANAGED ACCESS
  COMMENT = 'Staging layer for transformed metrics';

CREATE SCHEMA IF NOT EXISTS YT_SF_PROD.MART WITH MANAGED ACCESS
  COMMENT = 'Presentation layer for visualizations';
