# ADR-007: Introduction of a Dedicated Reporting Warehouse

## Status
Accepted

## Context
As the YouTube Metrics Pipeline expands to include a robust visualization layer (Streamlit) querying the presentation (`MART`) models, there is a risk of resource contention. The existing `YT_SF_TRANSFORM_WH` is heavily utilized by `dbt` for daily and incremental transformations, while the `YT_SF_LOAD_WH` handles Snowpark API extractions. 

To ensure low-latency query performance for dashboards without impacting back-end ETL operations, a dedicated reporting/BI compute resource is necessary. Additionally, the reporting layer must be restricted via the Principle of Least Privilege so it can only read fully modeled presentation data.

## Decision
We are introducing a dedicated **Reporting Warehouse** with strict cost controls and a dedicated functional role.

### Compute Infrastructure
- **Warehouse:** `YT_SF_REPORTING_WH`
- **Size:** `XSMALL` (1 credit/hour)
- **Auto-Suspend:** `60` seconds.
- **Resource Monitor:** `YT_SF_REPORTING_RM` capped at **15 Credits/month** to allow for project growth while strictly bounding costs.

### Role-Based Access Control (RBAC)
- **Functional Role:** `YT_SF_{ENV}_REPORTING_ROLE`
- **Privileges:** 
    - `USAGE` on the new `YT_SF_REPORTING_WH`.
    - `_SR` (Schema Read) strictly on the `MART` schema. It does not have access to `STAGING`, `RAW`, or `LANDING`.
    - Inherits up to `YT_SF_{ENV}_ADMIN_ROLE` to maintain centralized governance.

### Implementation Checklist
The following setup scripts must be modified by the developer to implement this architectural change:
1.  `.setup/snowflake/00_infrastructure_init.sql`: Define `YT_SF_REPORTING_WH` and `YT_SF_REPORTING_RM`.
2.  `.setup/snowflake/01_role_init.sql`: Define `YT_SF_DEV_REPORTING_ROLE` and `YT_SF_PROD_REPORTING_ROLE`.
3.  `.setup/snowflake/02_grant_init.sql`: Map `MART` schema `_SR` role to the new reporting roles, grant `USAGE` on the warehouse, and build the role hierarchy.
4.  `.setup/snowflake/03_user_init.sql`: Define a machine user (`YT_SF_REPORTING_USER`) and grant it the reporting roles.

## Consequences
- **Positive:** Perfect workload isolation between ETL and BI. If a heavy dashboard is refreshed, it will not slow down dbt models, and vice versa.
- **Positive:** Improved security. BI tools and reporting users can only see finalized data in the `MART` schema, preventing unauthorized access to raw payloads.
- **Negative:** Increased management overhead (tracking a 4th resource monitor) and potential for up to 15 additional credits of spend per month.
