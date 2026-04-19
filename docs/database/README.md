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

* **`YT_SF_CICD_WH`**: Shared by CI/CD orchestrated deployments and automated data ingestion scripts.
* **`YT_SF_TRANSFORM_WH`**: Used for data transformations using dbt, as well as manual querying and analytical processes.

### Cost Controls (Resource Monitors)
Both warehouses are strictly configured to prevent runaway costs:
* **Size**: `XSMALL` (consuming exactly 1 credit per hour).
* **Auto-Suspend**: Configured to `60` seconds to minimize billing when idle.
* **Monthly Quota Cap**: A Resource Monitor (`YT_SF_CICD_RM` and `YT_SF_TRANSFORM_RM`) is attached to each warehouse, capping spending at **2 Credits per month** per warehouse (~5 EUR). 
    * At 80% usage, an alert constraint triggers. 
    * At 100% usage, the warehouses are hard-suspended to prevent further billing.

---

## 3. Security & RBAC Model

The environment utilizes a modern two-tier Role-Based Access Control hierarchy, leveraging underlying "Object Roles" mapped upwards into broader "Functional Roles".

### 3.1 Schema Object Roles
For every schema (`LANDING`, `RAW`, `STAGING`, `MART`), three distinct access profiles reside underneath the hood:
- **`_SR` (Schema Read)**: Grants `USAGE`, `SELECT`, and `READ` on all existing/future objects.
- **`_SW` (Schema Write)**: Inherits `_SR`, and adds `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, and `WRITE`.
- **`_SFULL` (Schema Full)**: Inherits `_SW`, and adds `CREATE TABLE/VIEW` capability as well as `OWNERSHIP`.

### 3.2 Functional Roles (Users are assigned here)
The underlying Schema Object Roles are then distributed to the following Functional profiles based strictly on the principles of least privilege:

1. **`YT_SF_ADMIN_ROLE`** 
    * ***Purpose:*** System governance and top-level administration. 
    * ***Grants:*** Mapped to `_SFULL` everywhere. Owns the database, all schemas, and warehouses.
2. **`YT_SF_CICD_ROLE`**
    * ***Purpose:*** CI/CD deployment orchestrator.
    * ***Grants:*** Mapped to `_SFULL` everywhere. This permits tools like GitHub Actions to automate migrations and drop/create assets universally across all layers.
3. **`YT_SF_LOAD_ROLE`**
    * ***Purpose:*** Python pipeline extraction tasks.
    * ***Grants:*** Mapped to `_SFULL` on `LANDING` only. This role builds transient tables for API drops, but relies downstream on dbt to pull it into the warehouse history.
4. **`YT_SF_TRANSFORM_ROLE`**
    * ***Purpose:*** Data Build Tool (dbt) processing and manual querying.
    * ***Grants:*** Mapped to `_SFULL` on `RAW`, `STAGING`, and `MART`. Manages merging the staging drops into persistent history and compiling the analytical models.

*Inheritance:* All custom functional roles automatically roll up into the native Snowflake `SYSADMIN` role. This allows Account-level administrators to oversee the architecture natively without borrowing external roles.

### Machine Users & Authentication
Passwords are intentionally disabled. Authentication relies entirely on Key-Pair (RSA) authentication to ensure robust security for automated processes.

* **`YT_SF_CICD_USER`**: Machine user serving `YT_SF_CICD_ROLE`.
* **`YT_SF_LOAD_USER`**: Machine user serving `YT_SF_LOAD_ROLE`.
* **`YT_SF_DBT_USER`**: Service user serving `YT_SF_TRANSFORM_ROLE`.

---

## 4. Initialization Scripts
To recreate this environment from scratch identically, simply execute the scripts within `.setup/snowflake/` in numerical order using an administrative user (e.g., `ACCOUNTADMIN`):
1. `00_infrastructure_init.sql` *(Execution: ACCOUNTADMIN -> SYSADMIN)*
2. `01_role_init.sql` *(Execution: SECURITYADMIN)*
3. `02_grant_init.sql` *(Execution: SECURITYADMIN. NOTE: This executes the Object Role paradigm)*
4. `03_user_init.sql` *(Execution: SECURITYADMIN)*
