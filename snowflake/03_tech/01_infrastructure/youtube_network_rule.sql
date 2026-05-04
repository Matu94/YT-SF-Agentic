-- 1. Network Rule: Whitelist the YouTube Data API v3 endpoint
-- Resides in TECH schema of the current database.

CREATE OR REPLACE NETWORK RULE TECH.YOUTUBE_API_NETWORK_RULE
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('youtube.googleapis.com', 'www.googleapis.com')
  COMMENT = 'Allows outbound HTTPS traffic to the YouTube Data API v3 ({{SNOWFLAKE_ENVIRONMENT}})';
