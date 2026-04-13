# Data Architecture: YouTube Metrics Pipeline

## 1. Snowflake Environment Architecture
**Database and Schema Design:**
To maintain strict separation between workloads, the foundation will rely on entirely distinct databases for Development/Testing and Production.

*   **Production Environment:**
    *   Database: `YT_METRICS_PROD`
    *   Schemas:
        *   `LANDING` (Layer 1): Transient landing area for the Python extraction script. Stores raw API responses and uses a delete/insert method for daily updates.
        *   `RAW` (Layer 2): Persistent historical storage layer. Stores all data including historical loads, updating existing records from the `LANDING` layer.
        *   `STAGING` (Layer 3): Processing layer where required calculations are performed and correct column formats/data types are applied.
        *   `MART` (Layer 4): Presentation layer for different visualizations (e.g., Streamlit). *Note: As the project is currently simple, these visualization models can essentially be lightweight views built directly on top of Layer 3.*
*   **Development & Testing Environment:**
    *   Database: `YT_METRICS_DEV` (or feature-branch specific databases like `YT_METRICS_DBT_PR_123` for CI/CD).
    *   Schemas: Replicates the `LANDING`, `RAW`, `STAGING`, and `MART` structure, allowing engineers to test schema changes and validate models without risking production stability.

**Warehouse Sizing Strategy:**
Since the pipeline will run strictly 1x/day as a batch load, and the data volume is minimal to moderate (initially a few channels, capping at 20-30 for Version 1.0), an **X-Small (X-SMALL)** Snowflake Virtual Warehouse is mandated. This provides more than enough compute for flattening JSON and executing daily dimensional modeling while optimizing for cost efficiency.

## 2. Data Modeling Strategy (dbt Layer)
The hierarchical mapping of **Organization > Team > Channel** will be treated as cleanly maintained static metadata.

*   **Hierarchy Ingestion:** Maintain a `channels_hierarchy.csv` in the `seeds/` directory of the dbt project. This seed maps `channel_id` to its respective `channel_name`, `team_name`, and `organization_name`.
*   **Data Flow & Joins:**
    1.  dbt materialize this CSV into Snowflake as a static table (e.g., `seed_channels_hierarchy`).
    2.  The Python extraction script pushes raw API JSON data into transient tables in the `LANDING` schema using delete/insert logic.
    3.  dbt merges new data from `LANDING` into the `RAW` schema, preserving historical entries and updating changed records.
    4.  The `STAGING` layer standardizes column formats, executes required calculations, and deduplicates the persistent raw data.
    5.  In the `MART` visualization layer, fact models join the clean `STAGING` metrics against the `seed_channels_hierarchy` to support smooth aggregation in the BI layer.

## 3. Historical Backfill Mechanism
To safely onboard historical video and channel data as requested in the PRD:
*   **Separate Extraction Logic:** A dedicated backfill parameter or routine in the Python script will allow targeted retrieval of historical dates, bypassing the daily incremental logic.
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
    *   **Metrics:** Standard numerical fields (views, subscribers) must have `>= 0` value constraints.

## 5. Security Standards
*   **No Hardcoded Credentials:** Under no circumstances will any API keys, Snowflake passwords, or sensitive connection strings be hardcoded into Python source code, dbt profiles, or Streamlit configurations.
*   **Environment Variables:** All environments must rely entirely on environment variables (`.env` files for local development, and secure secret managers or injected CI/CD variables for automated/production runs).
