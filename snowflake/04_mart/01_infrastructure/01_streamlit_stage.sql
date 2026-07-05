-- ==============================================================
-- 01_streamlit_stage.sql
-- Stage for Snowflake Native Streamlit application files
--
-- PURPOSE:
--   Creates the stage in the MART schema to store the Streamlit
--   python, yaml, and pages files.
-- ==============================================================

USE DATABASE {{SNOWFLAKE_DATABASE}};
USE SCHEMA MART;

CREATE STAGE IF NOT EXISTS STREAMLIT_STAGE
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Stage for storing Snowflake Native Streamlit application files';
