# Snowflake Database Architecture & Configuration

This document outlines the Snowflake environment's infrastructure, compute resources, and Role-Based Access Control (RBAC) designed for the YouTube Metrics pipeline.

## 1. Storage Infrastructure 

The environment utilizes two dedicated, identically structured databases enforcing a Kimball dimensional modeling approach to cleanly separate development/testing workloads from production data.

### Databases
* **`YT_SF_DEV`**: The development environment used for CI/CD pipelines, feature branch testing, and local dbt development.
* **`YT_SF_PROD`**: The production database housing all live, validated YouTube metrics data serving end-users.

### Managed Access Schemas
All schemas are created `WITH MANAGED ACCESS`. This means object privileges are centrally managed by the schema owner (`YT_SF_ADMIN_ROLE`) rather than the individual user who created the table or view.
 
* **`LANDING`**: Transient landing area. Used by the Python ingestion script to dump raw JSON payloads directly from the API.
* **`RAW`**: Persistent historical storage. Retains a complete, untruncated history of all ingested data over time.
* **`STAGING`**: The transformation layer. Where JSON is flattened, data types are cast, and daily deltas/calculations are performed using dbt.
* **`MART`**: The presentation layer. Houses the final clean dimensional tables (Star Schema) optimized for Streamlit visualizations.
* **`TECH`**: The technical tracking schema. Dedicated entirely to CI/CD state management and administrative logs (e.g., tracking applied deployment files).
* **`TECH_BKP`**: The backup schema. A safe sandbox for manual snapshots of any object (tables cloned with `CREATE TABLE ... CLONE`, stored procedures, ad-hoc query results) before risky migrations or DDL changes. Objects here are **never** touched by automated pipelines.

## 2. Compute Infrastructure (Virtual Warehouses)

Operations are split across dedicated warehouses to allow for workload isolation without encountering concurrency bottlenecks.

* **`YT_SF_CICD_WH`**: Dedicated orchestrator warehouse for GitHub Actions to run DDL scripts.
* **`YT_SF_LOAD_WH`**: Dedicated warehouse for the Python data extraction and landing loads.
* **`YT_SF_TRANSFORM_WH`**: Used for data transformations using dbt, as well as manual querying and analytical processes.
* **`YT_SF_ADMIN_WH`**: Dedicated backend warehouse for administrative/maintenance tasks and debugging.

### Cost Controls (Resource Monitors)
Both runtime properties and financial bounds are uniformly enforced across all warehouses to prevent runaway costs:
* **Size**: `XSMALL` (consuming exactly 1 credit per hour).
* **Auto-Suspend**: Configured to `60` seconds to minimize billing when idle.
* **Monthly Quota Cap**: A Resource Monitor (`YT_SF_CICD_RM`, `YT_SF_LOAD_RM`, `YT_SF_TRANSFORM_RM`, `YT_SF_ADMIN_RM`) is independently attached to each warehouse, capping spending at **~5 EUR per month** per warehouse (roughly 2-5 Credits depending on enterprise tiering).
    * At 80% usage, an alert constraint triggers. 
    * At 100% usage, the warehouses are hard-suspended to prevent further billing.

---

## 3. Security & RBAC Model

The environment utilizes a modern two-tier Role-Based Access Control hierarchy, leveraging underlying "Object Roles" mapped upwards into broader "Functional Roles".

### 3.1 Schema Object Roles
For every schema (`LANDING`, `RAW`, `STAGING`, `MART`, `TECH`, `TECH_BKP`), three distinct access profiles reside underneath the hood:
- **`_SR` (Schema Read)**: Grants `USAGE`, `SELECT`, and `READ` on all existing/future objects.
- **`_SW` (Schema Write)**: Inherits `_SR`, and adds `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, and `WRITE`.
- **`_SFULL` (Schema Full)**: Inherits `_SW`, and adds `CREATE TABLE/VIEW/STAGE/TASK/DYNAMIC TABLE` capability. Holds `OWNERSHIP` over standard objects (Tables, Views, Stages, etc). *(Note: Compute objects like Tasks, Dynamic Tables, and Streamlits bypass this and are owned directly by Functional Roles).*

### 3.2 Functional Roles (Users are assigned here)
The underlying Schema Object Roles are then distributed to the following Functional profiles based strictly on the principles of least privilege:

1. **`YT_SF_{ENV}_ADMIN_ROLE`** 
    * ***Purpose:*** System governance and top-level administration for that specific environment.
    * ***Grants:*** Mapped to `_SFULL` everywhere. Owns the databases, all schemas, and warehouses. Holds the powerful `MANAGE GRANTS` global privilege to control security natively. All other functional roles explicitly roll up into this role.
2. **`YT_SF_{ENV}_CICD_ROLE`**
    * ***Purpose:*** CI/CD deployment orchestrator.
    * ***Grants:*** Mapped to `_SFULL` everywhere. This permits tools like GitHub Actions to automate migrations and drop/create assets universally across all layers for its respective environment. Holds `EXECUTE TASK` globally.
3. **`YT_SF_{ENV}_LOAD_ROLE`**
    * ***Purpose:*** Python pipeline extraction tasks.
    * ***Grants:*** Mapped to `_SFULL` on `LANDING` only. Permanently owns all future Tasks and Dynamic Tables within the `LANDING` schemas.
4. **`YT_SF_{ENV}_TRANSFORM_ROLE`**
    * ***Purpose:*** Data Build Tool (dbt) processing and manual querying.
    * ***Grants:*** Mapped to `_SFULL` on `RAW`, `STAGING`, and `MART`. Holds `EXECUTE TASK` globally. Permanently owns all future Tasks, Dynamic Tables, and Streamlits downstream of `LANDING`.

> **`TECH_BKP` Access Policy:** Only `ADMIN_ROLE` receives `_SFULL` on `TECH_BKP`. `CICD_ROLE` receives `_SR` (read-only). `LOAD_ROLE` and `TRANSFORM_ROLE` have **no access** to this schema. This ensures automated pipelines can never accidentally overwrite or read from backup objects.

*Inheritance:* The `LOAD`, `CICD`, and `TRANSFORM` functional roles automatically roll up into the environment's `ADMIN` role. The `ADMIN` role then maps into the native Snowflake `SYSADMIN`. This ensures the Admin can act upon any downstream objects inherently.

### Machine Users & Authentication
Passwords are intentionally disabled. Authentication relies entirely on Key-Pair (RSA) authentication to ensure robust security for automated processes.

* **`YT_SF_CICD_USER`**: Machine user assigned both `YT_SF_PROD_CICD_ROLE` and `YT_SF_DEV_CICD_ROLE` to execute pipelines identically across both environments.
* **`YT_SF_LOAD_USER`**: Machine user assigned both `YT_SF_PROD_LOAD_ROLE` and `YT_SF_DEV_LOAD_ROLE`.
* **`YT_SF_DBT_USER`**: Service user assigned both `YT_SF_PROD_TRANSFORM_ROLE` and `YT_SF_DEV_TRANSFORM_ROLE`.

---

## 4. External Network Access (Snowpark)

To allow Snowpark Python Stored Procedures to call the YouTube Data API, Snowflake's External Network Access stack is configured in the `TECH` schema of each environment.

| Object | Name | Location | Purpose |
|:---|:---|:---|:---|
| **Network Rule** | `YOUTUBE_API_NETWORK_RULE` | `{ENV}.TECH` | Whitelists outbound HTTPS to `youtube.googleapis.com` |
| **Secret** | `YOUTUBE_API_KEY_SECRET` | `{ENV}.TECH` | Stores the YouTube Data API v3 key securely |
| **Integration** | `YT_SF_{ENV}_YOUTUBE_API_INTEGRATION` | Account-level | Binds the Network Rule + Secret, attached to procedures |

**Role Privileges:**
- `YT_SF_{ENV}_ADMIN_ROLE`: Owns and manages the Network Rule, Secret, and Integration (has `CREATE INTEGRATION` account-level privilege).
- `YT_SF_{ENV}_LOAD_ROLE`: Has `USAGE` on the Integration and `READ` on the Secret — the minimum required to execute procedures that call the YouTube API.
- `YT_SF_{ENV}_CICD_ROLE`: Has `USAGE` on the Integration and `READ` on the Secret — required to deploy `CREATE OR REPLACE PROCEDURE` statements that reference the integration.

> ⚠️ **Secret Initialization**: The `YOUTUBE_API_KEY_SECRET` is created with a placeholder value (`YOUR_YOUTUBE_API_KEY_HERE`) in script `04_external_access.sql`. The real API key must be injected manually via the Snowsight UI or CLI before the first pipeline run and must **never** be committed to version control.

---

## 5. Initialization Scripts
To recreate this environment from scratch identically, execute the scripts within `.setup/snowflake/` in numerical order using an administrative user (e.g., `ACCOUNTADMIN`):
1. `00_infrastructure_init.sql` *(Execution: ACCOUNTADMIN -> SYSADMIN)*
2. `01_role_init.sql` *(Execution: SECURITYADMIN)*
3. `02_grant_init.sql` *(Execution: SECURITYADMIN. NOTE: This executes the Object Role paradigm)*
4. `03_user_init.sql` *(Execution: SECURITYADMIN)*
5. `04_external_access.sql` *(Execution: ADMIN_ROLE per environment. NOTE: Replace API key placeholder before running!)*
