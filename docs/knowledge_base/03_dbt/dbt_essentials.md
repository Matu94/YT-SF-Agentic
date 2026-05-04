# dbt Essentials: The Data Transformation Layer

dbt (data build tool) is the "T" in **ELT** (Extract, Load, Transform). It does not move data from one place to another; instead, it provides a framework to transform data that is already inside your warehouse (Snowflake) using SQL.

## 1. Core Syntax: Beyond Plain SQL
The power of dbt comes from mixing SQL with **Jinja** (a Python-based templating language). This allows your code to be dynamic and aware of its environment.

*   **`{{ source('schema', 'table') }}`**: Connects your models to the raw data in the `LANDING` or `RAW` schemas. It creates a formal dependency between dbt and the outside world.
*   **`{{ ref('model_name') }}`**: This is the "magic" of dbt. It links one model to another. Instead of hardcoding `FROM YT_SF_PROD.STAGING.stg_videos`, you use `FROM {{ ref('stg_videos') }}`. dbt uses these references to build a **Lineage Graph** and ensure tables are built in the correct order.
*   **Macros**: Reusable snippets of code. For example, we might create a macro to parse YouTube's ISO 8601 duration strings into seconds across multiple models.

## 2. Project Organization
A dbt project is structured to enforce modularity:
*   **`models/`**: The heart of the project. Contains the SQL files for transformations.
*   **`seeds/`**: CSV files that are loaded into Snowflake as tables. We use this for our `channels_hierarchy.csv` to map channels to Organizations and Teams.
*   **`snapshots/`**: Specialized logic for **SCD Type 2** tracking (see below).
*   **`macros/`**: Custom logic to extend SQL functionality.

## 3. Materializations: How Data is Stored
Every model in dbt can be configured to exist in Snowflake in different ways:
*   **View** (`materialized='view'`): A virtual table. It runs the query every time it's accessed. We use these in `STAGING` for lightweight cleanup.
*   **Table** (`materialized='table'`): A physical table that is dropped and recreated on every run. Best for final `MART` models that need fast read performance.
*   **Incremental** (`materialized='incremental'`): The most advanced type. It only appends or updates *new* data since the last run. This is essential for our `RAW` and `STAGING` layers to handle large volumes of daily YouTube metrics without re-processing history.

## 4. The YouTube Pipeline Flow (Kimball Mapping)
We use dbt to move data through the Kimball layers defined in our architecture:
1.  **Staging (`stg_`)**: Standardizes raw JSON from Landing. Renames columns to snake_case and casts data types (e.g., strings to integers).
2.  **Intermediate (`int_`)**: Where complex logic happens, such as calculating daily deltas (Today's Views - Yesterday's Views) using window functions.
3.  **Mart (`fct_`, `dim_`)**: The final Star Schema. Joining metrics with channel metadata to serve the Streamlit app.

## 5. Snapshots: Tracking Channel History (SCD Type 2)
If a YouTube channel changes its name or Niche, we don't want to overwrite the old data. 
*   **dbt Snapshots** look at the source data and identify changes.
*   They add `dbt_valid_from` and `dbt_valid_to` columns.
*   This allows our `dim_channel` to show exactly what a channel's metadata was on any specific day in the past.

## 6. Testing & Documentation: Trusting the Data
dbt allows us to define "Expectations" in a `schema.yml` file:
*   **Unique/Not Null**: Ensuring every video ID is unique.
*   **Relationships**: Ensuring every video in our fact table actually belongs to a known channel.
*   **Custom Tests**: Checking that `daily_views` is never a negative number.

## 7. Lineage & The Documentation Site
The most powerful feature for a beginner to explore is the **Lineage Graph**. 
*   By running `dbt docs generate` and `dbt docs serve`, dbt creates a local website.
*   It shows a visual map of how data flows from your `sources` through `staging` and finally into `marts`.
*   This makes it impossible to "lose" a column or wonder where a calculation came from. Every model is documented, and every dependency is visible.

---
*Created by **Data Engineer** — Precision Builder*
