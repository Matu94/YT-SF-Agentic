-- ==============================================================
-- 05_git_integration.sql
-- Snowflake Native Git Integration
--
-- PURPOSE:
--   Configures Snowflake's native Git Integration to allow Snowsight Workspaces
--   and direct execution of code (e.g., dbt, Snowpark) from the GitHub repository.
--
-- EXECUTION ROLE: YT_SF_PROD_ADMIN_ROLE / YT_SF_DEV_ADMIN_ROLE
--   (Requires CREATE INTEGRATION granted during 02_grant_init.sql)
--
-- IMPORTANT:
--   The SECRET objects contain a placeholder Personal Access Token (PAT).
--   You MUST replace 'YOUR_GITHUB_PAT_HERE' with your actual
--   GitHub PAT (with repo read/write access) before running this script.
--   Never commit the real PAT to version control.
--
-- OBJECT LOCATIONS:
--   All objects reside in the TECH schema (infrastructure layer).
--   Secret:          YT_SF_{ENV}.TECH.GITHUB_TOKEN_SECRET
--   API Integration: YT_SF_{ENV}_GITHUB_API_INTEGRATION
--   Git Repository:  YT_SF_{ENV}.TECH.YT_SF_AGENTIC_REPO
-- ==============================================================


-- ==============================================================
-- PROD Environment
-- ==============================================================
USE ROLE YT_SF_PROD_ADMIN_ROLE;

-- 1. Secret: Securely store the GitHub Personal Access Token
--    !! REPLACE THE PLACEHOLDER BEFORE EXECUTING !!
CREATE OR REPLACE SECRET YT_SF_PROD.TECH.GITHUB_TOKEN_SECRET
  TYPE = PASSWORD
  USERNAME = 'Matu94'
  PASSWORD = 'YOUR_GITHUB_PAT_HERE'
  COMMENT = 'GitHub PAT for Snowflake Git Integration (PROD)';

-- 2. API Integration: Handshake with GitHub
CREATE OR REPLACE API INTEGRATION YT_SF_PROD_GITHUB_API_INTEGRATION
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/Matu94')
  ALLOWED_AUTHENTICATION_SECRETS = (YT_SF_PROD.TECH.GITHUB_TOKEN_SECRET)
  ENABLED = TRUE
  COMMENT = 'PROD integration for GitHub repository access';

-- 3. Git Repository Object: Link Snowflake to the repo
CREATE OR REPLACE GIT REPOSITORY YT_SF_PROD.TECH.YT_SF_AGENTIC_REPO
  API_INTEGRATION = YT_SF_PROD_GITHUB_API_INTEGRATION
  GIT_CREDENTIALS = YT_SF_PROD.TECH.GITHUB_TOKEN_SECRET
  ORIGIN = 'https://github.com/Matu94/YT-SF-Agentic.git'
  COMMENT = 'YT-SF-Agentic GitHub repository (PROD)';

-- 4. Grant READ access to operational roles
--    This allows dbt, python extraction, and CI/CD to read code from the repo
GRANT READ ON GIT REPOSITORY YT_SF_PROD.TECH.YT_SF_AGENTIC_REPO TO ROLE YT_SF_PROD_TRANSFORM_ROLE;
GRANT READ ON GIT REPOSITORY YT_SF_PROD.TECH.YT_SF_AGENTIC_REPO TO ROLE YT_SF_PROD_CICD_ROLE;
GRANT READ ON GIT REPOSITORY YT_SF_PROD.TECH.YT_SF_AGENTIC_REPO TO ROLE YT_SF_PROD_LOAD_ROLE;


-- ==============================================================
-- DEV Environment
-- ==============================================================
USE ROLE YT_SF_DEV_ADMIN_ROLE;

-- 1. Secret (DEV)
--    !! REPLACE THE PLACEHOLDER BEFORE EXECUTING !!
CREATE OR REPLACE SECRET YT_SF_DEV.TECH.GITHUB_TOKEN_SECRET
  TYPE = PASSWORD
  USERNAME = 'Matu94'
  PASSWORD = 'YOUR_GITHUB_PAT_HERE'
  COMMENT = 'GitHub PAT for Snowflake Git Integration (DEV)';

-- 2. API Integration (DEV)
CREATE OR REPLACE API INTEGRATION YT_SF_DEV_GITHUB_API_INTEGRATION
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/Matu94')
  ALLOWED_AUTHENTICATION_SECRETS = (YT_SF_DEV.TECH.GITHUB_TOKEN_SECRET)
  ENABLED = TRUE
  COMMENT = 'DEV integration for GitHub repository access';

-- 3. Git Repository Object (DEV)
CREATE OR REPLACE GIT REPOSITORY YT_SF_DEV.TECH.YT_SF_AGENTIC_REPO
  API_INTEGRATION = YT_SF_DEV_GITHUB_API_INTEGRATION
  GIT_CREDENTIALS = YT_SF_DEV.TECH.GITHUB_TOKEN_SECRET
  ORIGIN = 'https://github.com/Matu94/YT-SF-Agentic.git'
  COMMENT = 'YT-SF-Agentic GitHub repository (DEV)';

-- 4. Grant READ access to operational roles (DEV)
GRANT READ ON GIT REPOSITORY YT_SF_DEV.TECH.YT_SF_AGENTIC_REPO TO ROLE YT_SF_DEV_TRANSFORM_ROLE;
GRANT READ ON GIT REPOSITORY YT_SF_DEV.TECH.YT_SF_AGENTIC_REPO TO ROLE YT_SF_DEV_CICD_ROLE;
GRANT READ ON GIT REPOSITORY YT_SF_DEV.TECH.YT_SF_AGENTIC_REPO TO ROLE YT_SF_DEV_LOAD_ROLE;
