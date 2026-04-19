USE ROLE SECURITYADMIN;

-- 1. Create a machine user for CI/CD process
CREATE USER IF NOT EXISTS YT_SF_CICD_USER
  DEFAULT_ROLE = YT_SF_CICD_ROLE
  DEFAULT_WAREHOUSE = YT_SF_CICD_WH
  MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE YT_SF_CICD_ROLE TO USER YT_SF_CICD_USER;

-- 2. Create a user for Transformation (e.g., dbt Cloud or human manual transformation user)
CREATE USER IF NOT EXISTS YT_SF_DBT_USER
  DEFAULT_ROLE = YT_SF_TRANSFORM_ROLE
  DEFAULT_WAREHOUSE = YT_SF_TRANSFORM_WH
  MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE YT_SF_TRANSFORM_ROLE TO USER YT_SF_DBT_USER;

-- 3. Create a user for Python data ingestion process
CREATE USER IF NOT EXISTS YT_SF_LOAD_USER
  DEFAULT_ROLE = YT_SF_LOAD_ROLE
  DEFAULT_WAREHOUSE = YT_SF_CICD_WH -- the load script shares the pipeline warehouse
  MUST_CHANGE_PASSWORD = FALSE;

GRANT ROLE YT_SF_LOAD_ROLE TO USER YT_SF_LOAD_USER;

/* Keypair Auth Setup:
using OpenSSL on your local machine. Run these commands in your bash terminal:

openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_cicd_key.p8 -v2 aes-256-cbc
openssl rsa -in snowflake_cicd_key.p8 -pubout -out snowflake_cicd_key.pub

If you need a pair for the DBT user:
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_dbt_key.p8 -v2 aes-256-cbc
openssl rsa -in snowflake_dbt_key.p8 -pubout -out snowflake_dbt_key.pub
*/

-- Add the public key to the CI/CD user:
ALTER USER YT_SF_CICD_USER
    SET RSA_PUBLIC_KEY = 'putyourpublichere_withouttheBEGINandENDPUBLICKEY_and_inoneline';

-- Add the public key to the Transform/dbt user:
ALTER USER YT_SF_DBT_USER
    SET RSA_PUBLIC_KEY = 'putyourpublichere_withouttheBEGINandENDPUBLICKEY_and_inoneline';
