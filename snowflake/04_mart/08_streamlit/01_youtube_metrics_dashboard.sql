-- ==============================================================
-- 01_youtube_metrics_dashboard.sql
-- Snowflake Native Streamlit Application
--
-- PURPOSE:
--   Creates or replaces the YouTube Metrics Dashboard Streamlit app
--   using the files uploaded to the STREAMLIT_STAGE.
-- ==============================================================

USE DATABASE {{SNOWFLAKE_DATABASE}};
USE SCHEMA MART;

CREATE OR REPLACE STREAMLIT YOUTUBE_METRICS_DASHBOARD
  ROOT_LOCATION = '@{{SNOWFLAKE_DATABASE}}.MART.STREAMLIT_STAGE'
  MAIN_FILE = 'Home.py'
  QUERY_WAREHOUSE = 'YT_SF_TRANSFORM_WH'
  COMMENT = 'YouTube metrics daily views dashboard';
