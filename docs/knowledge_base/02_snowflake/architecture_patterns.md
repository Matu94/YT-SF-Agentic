# Snowflake Architecture: The YouTube Pipeline Pattern

This document explains the core concepts of Snowflake and how they are applied in our YouTube Metrics Pipeline. It is designed as a primer for those new to the platform.

## 1. The Snowflake "Three-Layer" Architecture
Snowflake is unique because it separates **Storage**, **Compute**, and **Services**. This allows us to scale each part independently.

*   **Storage (S3/Azure/GCS)**: Data is stored centrally in an optimized, compressed format.
*   **Compute (Virtual Warehouses)**: This is the "Engine." Warehouses don't store data; they just process it.
*   **Cloud Services**: The "Brain" that handles security, metadata, and optimization.

## 2. Compute Isolation (Virtual Warehouses)
In our project, we use dedicated warehouses for different workloads to ensure they never "fight" for resources:
*   **`YT_SF_LOAD_WH`**: Dedicated only to the Python Snowpark extractions.
*   **`YT_SF_TRANSFORM_WH`**: Dedicated to dbt and analytical queries.
*   **`YT_SF_CICD_WH`**: Dedicated to automated deployments.
*   **`YT_SF_REPORTING_WH`**: Dedicated to BI tools and Streamlit visualizations to isolate read workloads from ETL processes.
*   **Resource Monitors**: Each warehouse is capped by a dedicated resource monitor (5 Credits/month for CI/CD & Admin, 15 Credits/month for Load, Transform, and Reporting) to prevent runaway costs as data volume grows—a Snowflake best practice for budget control.

## 3. The Medallion Data Flow & Dimensional Architecture
We follow the **Kimball Dimensional Modeling** approach, moving data through four logical layers:
1.  **LANDING (Transient)**: A "temporary parking lot" for raw JSON. We use `TRANSIENT` tables here to save on storage costs because the data is easily reproducible. All session and account operations enforce `Europe/Budapest` timezone context to prevent `CURRENT_DATE()` offset issues.
2.  **RAW (Persistent)**: The permanent "Source of Truth." Data is moved from Landing to Raw using incremental logic, preserving the entire historical record.
3.  **STAGING (Processing)**: This is the transformation layer. Since the YouTube API provides cumulative metrics (Total Views), Staging uses `LAG()` window functions to calculate discrete daily deltas (`Today - Yesterday`). Additionally, to prevent metrics from mapping prior to a video's publication date during intra-day runs, `metric_date` is strictly lower-bounded using `GREATEST(DATEADD(day, -1, CAST(extracted_at AS DATE)), CAST(CONVERT_TIMEZONE('UTC', 'Europe/Budapest', published_at) AS DATE))`.
4.  **MART (Presentation)**: The final **Star Schema** (Dimensions, Daily Facts, and Rolling 7-Day & 30-Day Periodic Snapshot Facts) denormalized into One Big Table (OBT) views (`rpt_video_performance_daily`, `rpt_channel_performance_daily`, `rpt_video_performance_rolling_7d`, `rpt_channel_performance_rolling_7d`, `rpt_video_performance_rolling_30d`, `rpt_channel_performance_rolling_30d`) optimized for Streamlit visualizations. Pre-aggregating 7-day and 30-day rolling metrics in the warehouse avoids expensive query-time window functions in the BI layer.

## 4. RBAC: Functional vs. Object Roles
Security in Snowflake is managed through **Role-Based Access Control (RBAC)**. We use a "Two-Tier" model:
*   **Object Roles**: (e.g., `_SR` for Read, `_SW` for Write). These are tied to specific schemas (Landing, Raw, etc.).
*   **Functional Roles**: (e.g., `LOAD_ROLE`, `TRANSFORM_ROLE`). These are what users (and machine users) are actually assigned.
*   **Hierarchy**: We grant Object Roles to Functional Roles. This makes security "Plug and Play." If you add a new data layer, you just update the Object Role, and every Functional Role that uses it inherits the access automatically.

## 5. Snowpark & External Network Access
Snowflake isn't just for SQL. We use **Snowpark (Python)** to call the YouTube API directly from within the warehouse.
*   **Network Rules**: Whitelist specific domains (`youtube.googleapis.com`).
*   **Secrets**: Store API keys securely in the `TECH` schema so they are never visible in code.
*   **External Access Integrations**: Bind the Rule and the Secret together, allowing our Python Stored Procedures to "reach out" to the internet securely.

## 6. Data Protection (Zero-Copy Cloning)
Our **`TECH_BKP`** schema leverages Snowflake's **Zero-Copy Cloning**.
*   **The Concept**: Cloning a table doesn't actually copy the data—it just copies the metadata (pointers). It is instantaneous and costs **zero storage** until the data in the clone is modified.
*   **Usage**: Our CI/CD pipeline clones tables to `TECH_BKP` before running risky migrations, providing a "safety net" that is both fast and cost-free.

---
*Created by **Principal Data Architect** — Strategic Visionary*

