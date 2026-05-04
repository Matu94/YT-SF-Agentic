-- Purpose: [Brief description of what this model/table does]
-- Author: [Persona Name or Human Name]
-- Created: {{CURRENT_DATE}}
-- Hierarchy: [e.g., Cérnagyár -> Fókusz Stúdió]
-- Layer: [LANDING | RAW | STAGING | MART]

/* 
  VARIABLE SUBSTITUTION REFERENCE:
  - {{SNOWFLAKE_DATABASE}}: Target database (YT_SF_DEV / YT_SF_PROD)
  - {{SNOWFLAKE_WAREHOUSE}}: Target warehouse (YT_SF_LOAD_WH / YT_SF_TRANSFORM_WH)
  - {{SNOWFLAKE_ENVIRONMENT}}: Environment name (DEV / PROD)
*/

-- [DDL Statement]
CREATE OR REPLACE TABLE [SCHEMA].[TABLE_NAME] (
    [COLUMN_NAME] [DATA_TYPE] [CONSTRAINTS],
    ...
    METADATA_INSERTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    METADATA_UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = '[Description for Snowflake Catalog]';

-- [Grants]
-- Note: Managed access schemas handle most grants, but specific object-level logic goes here if needed.
GRANT SELECT ON TABLE [SCHEMA].[TABLE_NAME] TO ROLE YT_SF_{{SNOWFLAKE_ENVIRONMENT}}_TRANSFORM_ROLE;
