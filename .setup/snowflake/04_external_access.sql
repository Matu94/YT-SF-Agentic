-- ==============================================================
-- 04_external_access.sql
-- External Network Access for Snowpark Python Stored Procedures
--
-- PURPOSE:
--   Configures Snowflake's External Network Access features to allow
--   Snowpark Python Stored Procedures to call the YouTube Data API.
--
-- EXECUTION ROLE: YT_SF_PROD_ADMIN_ROLE / YT_SF_DEV_ADMIN_ROLE
--   (Requires CREATE INTEGRATION granted during 02_grant_init.sql)
--
-- IMPORTANT:
--   The SECRET objects contain a placeholder API key.
--   You MUST replace 'YOUR_YOUTUBE_API_KEY_HERE' with your actual
--   YouTube Data API v3 key before running this script.
--   Never commit the real key to version control.
--
-- OBJECT LOCATIONS:
--   All objects reside in the TECH schema (infrastructure layer).
--   Network Rule:  YT_SF_{ENV}.TECH.YOUTUBE_API_NETWORK_RULE
--   Secret:        YT_SF_{ENV}.TECH.YOUTUBE_API_KEY_SECRET
--   Integration:   YT_SF_{ENV}_YOUTUBE_API_INTEGRATION
-- ==============================================================


-- ==============================================================
-- PROD Environment
-- ==============================================================
USE ROLE YT_SF_PROD_ADMIN_ROLE;
USE DATABASE YT_SF_PROD;
USE SCHEMA TECH;

-- 1. Network Rule: Whitelist the YouTube Data API v3 endpoint
CREATE OR REPLACE NETWORK RULE YOUTUBE_API_NETWORK_RULE
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('youtube.googleapis.com', 'www.googleapis.com')
  COMMENT = 'Allows outbound HTTPS traffic to the YouTube Data API v3';

-- 2. Secret: Securely store the YouTube API Key
--    !! REPLACE THE PLACEHOLDER BEFORE EXECUTING !!
CREATE OR REPLACE SECRET YOUTUBE_API_KEY_SECRET
  TYPE = GENERIC_STRING
  SECRET_STRING = 'YOUR_YOUTUBE_API_KEY_HERE'
  COMMENT = 'YouTube Data API v3 key for Snowpark ingestion procedures';

-- 3. External Access Integration: Bind the network rule and secret together
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION YT_SF_PROD_YOUTUBE_API_INTEGRATION
  ALLOWED_NETWORK_RULES = (YOUTUBE_API_NETWORK_RULE)
  ALLOWED_AUTHENTICATION_SECRETS = (YOUTUBE_API_KEY_SECRET)
  ENABLED = TRUE
  COMMENT = 'PROD integration granting Snowpark access to YouTube API';

-- 4. Grant USAGE on the integration and secret to the LOAD role
--    (Future procedures owned by LOAD_ROLE need these to authenticate)
GRANT USAGE ON INTEGRATION YT_SF_PROD_YOUTUBE_API_INTEGRATION TO ROLE YT_SF_PROD_LOAD_ROLE;
GRANT READ ON SECRET YT_SF_PROD.TECH.YOUTUBE_API_KEY_SECRET TO ROLE YT_SF_PROD_LOAD_ROLE;

-- Also grant to CICD so it can deploy procedures that reference the integration
GRANT USAGE ON INTEGRATION YT_SF_PROD_YOUTUBE_API_INTEGRATION TO ROLE YT_SF_PROD_CICD_ROLE;
GRANT READ ON SECRET YT_SF_PROD.TECH.YOUTUBE_API_KEY_SECRET TO ROLE YT_SF_PROD_CICD_ROLE;


-- ==============================================================
-- DEV Environment
-- ==============================================================
USE ROLE YT_SF_DEV_ADMIN_ROLE;
USE DATABASE YT_SF_DEV;
USE SCHEMA TECH;

-- 1. Network Rule (DEV)
CREATE OR REPLACE NETWORK RULE YOUTUBE_API_NETWORK_RULE
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('youtube.googleapis.com', 'www.googleapis.com')
  COMMENT = 'Allows outbound HTTPS traffic to the YouTube Data API v3 (DEV)';

-- 2. Secret (DEV)
--    !! REPLACE THE PLACEHOLDER BEFORE EXECUTING !!
CREATE OR REPLACE SECRET YOUTUBE_API_KEY_SECRET
  TYPE = GENERIC_STRING
  SECRET_STRING = 'YOUR_YOUTUBE_API_KEY_HERE'
  COMMENT = 'YouTube Data API v3 key for Snowpark ingestion procedures (DEV)';

-- 3. External Access Integration (DEV)
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION YT_SF_DEV_YOUTUBE_API_INTEGRATION
  ALLOWED_NETWORK_RULES = (YOUTUBE_API_NETWORK_RULE)
  ALLOWED_AUTHENTICATION_SECRETS = (YOUTUBE_API_KEY_SECRET)
  ENABLED = TRUE
  COMMENT = 'DEV integration granting Snowpark access to YouTube API';

-- 4. Grant USAGE on the integration and secret to the DEV LOAD role
GRANT USAGE ON INTEGRATION YT_SF_DEV_YOUTUBE_API_INTEGRATION TO ROLE YT_SF_DEV_LOAD_ROLE;
GRANT READ ON SECRET YT_SF_DEV.TECH.YOUTUBE_API_KEY_SECRET TO ROLE YT_SF_DEV_LOAD_ROLE;

-- Also grant to DEV CICD for procedure deployment
GRANT USAGE ON INTEGRATION YT_SF_DEV_YOUTUBE_API_INTEGRATION TO ROLE YT_SF_DEV_CICD_ROLE;
GRANT READ ON SECRET YT_SF_DEV.TECH.YOUTUBE_API_KEY_SECRET TO ROLE YT_SF_DEV_CICD_ROLE;


