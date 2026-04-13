# Data Architecture: YouTube Metrics Pipeline

## 1. Snowflake Environment Architecture
**Database and Schema Design:**
To align with the Phase 1 scope, the foundation will initially rely on a single Production database. Development and Testing environments will be introduced in future phases as the pipeline matures.

*   **Production Environment (Phase 1):**
    *   Database: `YT_METRICS_PROD`
    *   Schemas:
        *   `LANDING` (Layer 1): Transient landing area for the Python extraction script. Stores raw API responses and uses a delete/insert method for 1-2x daily updates.
        *   `RAW` (Layer 2): Persistent historical storage layer. Stores all data including historical loads, updating existing records from the `LANDING` layer.
        *   `STAGING` (Layer 3): Processing layer where required calculations are performed and correct column formats/data types are applied.
        *   `MART` (Layer 4): Presentation layer for different visualizations (e.g., Streamlit). *Note: As the project is currently simple, these visualization models can essentially be lightweight views built directly on top of Layer 3.*

**Warehouse Sizing Strategy:**
Since the pipeline will run 1-2 times per day as a batch load, and the data volume is minimal in Phase 1 (starting with 4 channels, expanding later), an **X-Small (X-SMALL)** Snowflake Virtual Warehouse is mandated. This provides more than enough compute for flattening JSON and executing dimensional modeling while optimizing for cost efficiency.

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
    2.  **Landing & Raw:** Python extracts push cumulative API metrics into `LANDING` transient tables. dbt merges this into the persistent `RAW` history.
    3.  **Staging (The Delta Calculation):** Because the YouTube API provides cumulative lifetime totals, the `STAGING` layer takes on the heavy lifting of calculating daily discrete performance. It will use window functions (e.g., `LAG()`) over the recorded `RAW` history to calculate daily deltas (e.g., `Today - Yesterday = Daily Growth`).
    4.  **Mart Aggregation:** In the `MART` layer, fact models join the clean `STAGING` metrics against the active SCD `dim_channel` records to feed the Streamlit dashboards efficiently.

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
    *   **Metrics:** Standard numerical fields (e.g., views, likes, comments, subscribers, duration) must have `>= 0` value constraints.

## 5. Security Standards
*   **No Hardcoded Credentials:** Under no circumstances will any API keys, Snowflake passwords, or sensitive connection strings be hardcoded into Python source code, dbt profiles, or Streamlit configurations.
*   **Environment Variables:** All environments must rely entirely on environment variables (`.env` files for local development, and secure secret managers or injected CI/CD variables for automated/production runs).
