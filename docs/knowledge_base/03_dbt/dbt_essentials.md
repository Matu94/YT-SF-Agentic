# dbt Essentials: The Data Transformation Layer

dbt (data build tool) is the "T" in ELT. It doesn't move data; it transforms it *inside* Snowflake using SQL.

## 1. The `profiles.yml`
*   **What is it?**: This is the "Connection String" for dbt. It tells dbt *where* your Snowflake account is and *how* to log in (User, Role, Warehouse).
*   **Why a template?**: We keep a `profiles.yml.template` in the repo to show the structure, but your actual credentials stay in `~/.dbt/profiles.yml` (outside the git repo) for security.

## 2. Models: The Building Blocks
In dbt, every `.sql` file in the `models/` folder is a "Model."
*   **Views vs. Tables**: 
    *   **Views** (`materialized='view'`) are virtual. They run the query every time you look at them. Great for Staging.
    *   **Tables** (`materialized='table'`) physically store the data. Great for Marts.
    *   **Incremental** (`materialized='incremental'`) only adds *new* rows since the last run. Essential for our `RAW` layer to handle large volumes of YouTube data efficiently.

## 3. SCD Type 2 (SCD2)
*   **The Problem**: If a YouTube channel changes its name from "Fókusz" to "Fókusz Stúdió," a standard table just overwrites it. You lose the history.
*   **The Solution**: SCD2 (Slowly Changing Dimension Type 2) adds new rows for changes and uses `valid_from` and `valid_to` timestamps.
*   **In this Project**: We use **dbt Snapshots** to automatically track these changes for `dim_channel`. You can see "who the channel was" at any point in time.

## 4. Ingesting "One Date" (Filtering)
To ingest or process only a specific date (e.g., during a backfill), we use **dbt Variables** or **Environment Variables**.
*   **Example**: `dbt run --select stg_youtube_stats --vars '{"target_date": "2024-05-01"}'`
*   Inside the SQL, we use: `WHERE metric_date = '{{ var("target_date") }}'`

---
*Created by **Data Engineer** — Precision Builder*
