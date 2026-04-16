USE ROLE SECURITYADMIN;

-- 1. Create custom roles
CREATE ROLE IF NOT EXISTS YT_SF_ADMIN_ROLE
  COMMENT = 'System Admin Duties: Owns DB, Schemas, Warehouses';

CREATE ROLE IF NOT EXISTS YT_SF_TRANSFORM_ROLE
  COMMENT = 'Transformation & Data Build Tool (dbt) role for processing and manual querying';

CREATE ROLE IF NOT EXISTS YT_SF_CICD_ROLE
  COMMENT = 'CI/CD pipeline role for automated deployment and python ingestion';

-- 2. Grant roles to SYSADMIN to maintain a robust RBAC hierarchy
-- This ensures Account Admins can natively oversee operations without explicitly borrowing these roles
GRANT ROLE YT_SF_ADMIN_ROLE TO ROLE SYSADMIN;
GRANT ROLE YT_SF_TRANSFORM_ROLE TO ROLE SYSADMIN;
GRANT ROLE YT_SF_CICD_ROLE TO ROLE SYSADMIN;
