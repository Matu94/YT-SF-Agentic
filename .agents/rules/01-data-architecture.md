# Data Architecture: YouTube Metrics Pipeline

## 1. Snowflake Environment Architecture
**Database and Schema Design:**
The foundation relies on two core environments: Development (`DEV`) and Production (`PROD`).

*   **Environments:**
    *   Databases: `YT_SF_DEV` and `YT_SF_PROD`
    *   Schemas (all configured `WITH MANAGED ACCESS` for centralized privilege control):
        *   `LANDING` (Layer 1): Transient landing area for Snowpark Python Stored Procedures. Stores raw API responses and uses a delete/insert method for 1-2x daily updates.
        *   `RAW` (Layer 2): Persistent historical storage layer. Stores all data including historical loads, updating existing records from the `LANDING` layer.
        *   `STAGING` (Layer 3): Processing layer where required calculations are performed and correct column formats/data types are applied.
        *   `MART` (Layer 4): Presentation layer for different visualizations (e.g., Streamlit). *Note: As the project is currently simple, these visualization models can essentially be lightweight views built directly on top of Layer 3.*
        *   `TECH` (Infrastructure): CI/CD deployment tracking, External Network Access objects (Secrets, Network Rules).
        *   `TECH_BKP` (Infrastructure): Manual backup sandbox. Holds cloned tables, ad-hoc snapshots, and any object copy created before a risky migration. Never touched by automated pipelines.

**Warehouse & Compute Strategy:**
To ensure workload isolation and prevent concurrency bottlenecks, compute is split across four dedicated **X-Small (X-SMALL)** Virtual Warehouses with 60-second auto-suspend:
*   `YT_SF_CICD_WH`: For automated deployments and CI/CD orchestration.
*   `YT_SF_LOAD_WH`: Dedicated compute for Snowflake Tasks running Snowpark Python Stored Procedures to extract API data into Landing.
*   `YT_SF_TRANSFORM_WH`: For dbt transformations and analytical querying.
*   `YT_SF_ADMIN_WH`: For database administration and maintenance.
*Cost Controls:* Each warehouse is strictly bound by its own Resource Monitor (`YT_SF_CICD_RM`, `YT_SF_LOAD_RM`, etc.), capping spend at ~5 EUR per month.

## 2. Data Modeling Strategy (dbt Layer)
The pipeline will adopt a Kimball Dimensional Modeling approach (Star Schema) in the presentation layer.

*   **Dimensional Modeling (MART Layer):**
    *   **Dimensions (Context):**
        *   `dim_channel`: Tracks changing channel metadata (e.g., title, description, organizational hierarchy). Implemented as a **Slowly Changing Dimension (SCD) Type 2** using **dbt Snapshots** to automatically track `valid_from` and `valid_to` history.
        *   `dim_video`: Captures video-level static data (duration, title, publish date).
        *   `dim_date`: Standard date dimension for Streamlit BI filtering.
    *   **Facts (Metrics):**
        *   `fct_daily_channel_metrics`: Captures channel-level metrics (e.g., total subscribers and calculated daily subscriber growth).
        *   `fct_daily_video_metrics`: Captures video-level engagement (e.g., views, likes, comments).

*   **Data Flow & Processing Logic:**
    1.  **Hierarchy Integration:** Organizational mapping (Organization > Team) is maintained via a `channels_hierarchy.csv` seed in dbt.
    2.  **Landing & Raw:** Snowflake Tasks execute Python Stored Procedures to pull cumulative API metrics directly into `LANDING` transient tables. dbt then merges this into the persistent `RAW` history.
    3.  **Staging (The Delta Calculation):** Because the YouTube API provides cumulative lifetime totals, the `STAGING` layer takes on the heavy lifting of calculating daily discrete performance. It will use window functions (e.g., `LAG()`) over the recorded `RAW` history to calculate daily deltas (e.g., `Today - Yesterday = Daily Growth`).
    4.  **Mart Aggregation:** In the `MART` layer, fact models join the clean `STAGING` metrics against the active SCD `dim_channel` records to feed the Streamlit dashboards efficiently.

## 3. Historical Backfill Mechanism
To safely onboard historical video and channel data as requested in the PRD:
*   **Separate Extraction Logic:** A dedicated backfill parameter or routine in the Snowpark Python Stored Procedure will allow targeted retrieval of historical dates, bypassing the daily incremental logic.
*   **Target Landing:** Historical data lands in the transient `LANDING` tables but will be tagged with a load-type metadata column (e.g., `_load_type = 'backfill'`). dbt will then merge it into the historical `RAW` tables.
*   **Idempotent Modeling:** The dbt models (specifically those built incrementally) will enforce idempotency using standard `unique_key` configurations (e.g., `['date', 'channel_id']`). When historical data arrives, dbt's next daily run will perform a seamless MERGE/UPSERT into the target tables, backfilling past dates without disrupting or duplicating the daily load.

## 4. dbt Standards & Testing
All dbt development must enforce strict naming conventions and quality checks:
*   **Naming Conventions:**
    *   Staging: `stg_<source>_<entity>` (e.g., `stg_youtube_channel_stats`).
    *   Dimensions: `dim_<business_entity>` (e.g., `dim_channels`).
    *   Facts: `fct_<business_process>` (e.g., `fct_daily_channel_performance`).
*   **Testing Requirements:**
    *   **Primary Keys:** Must implement strict `unique` and `not_null` tests.
    *   **Foreign Keys:** `channel_id` in fact models must pass `relationships` tests against the hierarchy dimension/seed table to catch orphaned data.
    *   **Metrics:** Standard numerical fields (e.g., views, likes, comments, subscribers, duration) must have `>= 0` value constraints.

## 5. Security, RBAC & Authentication Standards
*   **Role-Based Access Control (RBAC):** The environment implements a rigorous Snowflake RBAC model separating schema-level Object Roles (`_SR`, `_SW`, `_SFULL`) from broad Functional Roles:
    *   `YT_SF_ADMIN_ROLE`: Top-level governance (maps to SYSADMIN).
    *   `YT_SF_CICD_ROLE`: Pipeline deployment orchestration.
    *   `YT_SF_LOAD_ROLE`: Granted Write/Full access *only* to the `LANDING` schema. It natively owns and executes the Stored Procedures and Tasks.
    *   `YT_SF_TRANSFORM_ROLE`: Granted Write/Full access to `RAW`, `STAGING`, and `MART` for dbt operations.
*   **Authentication (Key-Pair):** Passwords are intentionally disabled for machine service users (`YT_SF_CICD_USER`, `YT_SF_LOAD_USER`, `YT_SF_DBT_USER`) in favor of RSA Key-Pair authentication.
*   **External Network Access & Secrets:** The YouTube API key must **never** be hardcoded. It will be securely stored natively inside a Snowflake `SECRET` object. A Snowflake `NETWORK RULE` and `EXTERNAL ACCESS INTEGRATION` will be bound to this secret, granting the Python Stored Procedure highly governed outbound access to the YouTube API.
