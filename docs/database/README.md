# Snowflake Database Architecture & Configuration

This document outlines the Snowflake environment's infrastructure, compute resources, and Role-Based Access Control (RBAC) designed for the YouTube Metrics pipeline.

## 1. Storage Infrastructure 

The environment uses a single production database structured into four layers, enforcing a Kimball dimensional modeling approach.

### Database
* **`YT_SF_PROD`**: The production database housing all YouTube metrics data.

### Managed Access Schemas
All schemas are created `WITH MANAGED ACCESS`. This means object privileges are centrally managed by the schema owner (`YT_SF_ADMIN_ROLE`) rather than the individual user who created the table or view.
 
* **`LANDING`**: Transient landing area. Used by the Python ingestion script to dump raw JSON payloads directly from the API.
* **`RAW`**: Persistent historical storage. Retains a complete, untruncated history of all ingested data over time.
* **`STAGING`**: The transformation layer. Where JSON is flattened, data types are cast, and daily deltas/calculations are performed using dbt.
* **`MART`**: The presentation layer. Houses the final clean dimensional tables (Star Schema) optimized for Streamlit visualizations.

## 2. Compute Infrastructure (Virtual Warehouses)

Operations are split across dedicated warehouses to allow for workload isolation without encountering concurrency bottlenecks.

* **`YT_SF_CICD_WH`**: Used strictly for the CI/CD pipeline (extracting/loading data via Python, deploying infrastructure). 
* **`YT_SF_TRANSFORM_WH`**: Used for data transformations using dbt, as well as manual querying and analytical processes.

### Cost Controls (Resource Monitors)
Both warehouses are strictly configured to prevent runaway costs:
* **Size**: `XSMALL` (consuming exactly 1 credit per hour).
* **Auto-Suspend**: Configured to `60` seconds to minimize billing when idle.
* **Monthly Quota Cap**: A Resource Monitor (`YT_SF_CICD_RM` and `YT_SF_TRANSFORM_RM`) is attached to each warehouse, capping spending at **2 Credits per month** per warehouse (~5 EUR). 
    * At 80% usage, an alert constraint triggers. 
    * At 100% usage, the warehouses are hard-suspended to prevent further billing.

## 3. Security & RBAC Model

The environment utilizes a custom Role-Based Access Control hierarchy, scaling strictly on the principles of least privilege.

### Roles and Duties
1. **`YT_SF_ADMIN_ROLE`** 
    * ***Purpose:*** System governance and top-level administration. 
    * ***Grants:*** Owns `YT_SF_PROD` and all 4 Managed Access Schemas. Owns both Virtual Warehouses.
2. **`YT_SF_CICD_ROLE`**
    * ***Purpose:*** CI/CD deployer and raw ingestion engine.
    * ***Grants:*** Has broad Create, Modify, and Select permissions universally across all schemas (`LANDING`, `RAW`, `STAGING`, `MART`). This permits CI/CD tools like GitHub Actions to deploy views, tasks, dynamic tables, pipelines, and Streamlit apps anywhere in the database.
3. **`YT_SF_TRANSFORM_ROLE`**
    * ***Purpose:*** Business logic execution (typically dbt) and manual querying.
    * ***Grants:*** Read-only access to `RAW`. Full read/write and object creation capabilities in `STAGING` and `MART`.

*Inheritance:* All three custom roles are rolled up into the native Snowflake `SYSADMIN` role. This allows Account level administrators to oversee the architecture natively without borrowing external roles.

### Machine Users & Authentication
Passwords are intentionally disabled. Authentication relies internally on Key-Pair (RSA) authentication to ensure robust security for automated processes.

* **`YT_SF_CICD_USER`**: Machine user assigned strictly to `YT_SF_CICD_ROLE` and `YT_SF_CICD_WH`.
* **`YT_SF_DBT_USER`**: Service user assigned strictly to `YT_SF_TRANSFORM_ROLE` and `YT_SF_TRANSFORM_WH`.

## 4. Initialization Scripts
To recreate this environment from scratch, execute the scripts within `.setup/snowflake/` in numerical order using a highly privileged administrative user (e.g., `ACCOUNTADMIN`):
1. `00_infrastructure_init.sql` (Creates DB, Warehouses, Resource Monitors, Schemas)
2. `01_role_init.sql` (Establishes role hierarchy)
3. `02_grant_init.sql` (Applies granular deployer/reader mappings)
4. `03_user_init.sql` (Provisions machine users and keypairs)
