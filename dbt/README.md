# YouTube Metrics dbt Project

This project manages the transformation and semantic layers of the YouTube Metrics Pipeline, following the Medallion architecture (Staging -> Mart).

## Architecture
- **Raw Layer (`models/raw/`)**: Managed as incremental models that ingest data from the `LANDING` transient tables.
- **Staging Layer (`models/staging/`)**: Handles JSON flattening, data cleaning, and daily delta calculations.
- **Mart Layer (`models/mart/`)**: Implements the Kimball Star Schema (Facts and Dimensions).
- **Snapshots (`snapshots/`)**: Implements SCD Type 2 tracking for channel metadata.

## Setup
1.  Copy `profiles.yml.template` to `~/.dbt/profiles.yml`.
2.  Set the following environment variables:
    - `SNOWFLAKE_ACCOUNT`
    - `SNOWFLAKE_USER`
    - `SNOWFLAKE_PRIVATE_KEY_PATH`
3.  Run `dbt debug` to verify connectivity.
