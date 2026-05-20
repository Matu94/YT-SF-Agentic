-- 2. Secret: Securely store the YouTube API Key
-- Resides in TECH schema. Placeholder value must be replaced manually in Snowsight.

CREATE OR REPLACE SECRET TECH.YOUTUBE_API_KEY_SECRET
  TYPE = GENERIC_STRING
  SECRET_STRING = '{{YOUTUBE_API_KEY}}'
  COMMENT = 'YouTube Data API v3 key for Snowpark ingestion procedures ({{SNOWFLAKE_ENVIRONMENT}})';
