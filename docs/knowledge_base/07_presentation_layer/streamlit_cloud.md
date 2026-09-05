# Presentation Layer: Streamlit Community Cloud

## 1. Overview
Our data presentation layer is built on **Streamlit**, a fast and intuitive Python framework for creating data apps. While Snowflake offers Streamlit-in-Snowflake (SiS), we strategically deploy our production dashboard to **Streamlit Community Cloud** (share.streamlit.io).

## 2. Architectural Motivation (ADR-010)
Running Streamlit directly inside Snowflake consumes Virtual Warehouse compute credits every time a user interacts with a filter or loads a page. For a public or heavily trafficked dashboard, this could lead to exponential compute costs.

To solve this, we decoupled the presentation layer from the analytical compute:
*   **Dev/Debug**: We still support SiS deployment (`@MART.STREAMLIT_STAGE`) for internal developer testing.
*   **Production**: We export the heavy dimensional models to static Parquet files hosted on AWS S3. Streamlit Community Cloud serves these Parquet files entirely in-memory, completely bypassing Snowflake compute.

## 3. The Dual-Mode Abstraction
The magic behind this flexibility is our custom `data_loader.py` module. It acts as an abstraction layer:
1.  **Snowflake Native Mode**: If the app detects it is running inside Snowflake (via `snowflake.snowpark.context.get_active_session`), it executes native SQL queries against the `MART` schema.
2.  **S3 Export Mode**: If it is running in Streamlit Cloud, it falls back to reading the pre-aggregated `.parquet` files from the AWS S3 bucket using `pandas.read_parquet`.

This allows the exact same Python UI code (`Home.py`, `1_Channel_Info.py`, etc.) to run seamlessly in both environments without modification.

## 4. Deploying to Streamlit Community Cloud
Streamlit Community Cloud pulls directly from GitHub.

### Setup Process:
1.  **Link GitHub**: Log into [share.streamlit.io](https://share.streamlit.io/) and connect your GitHub account.
2.  **Deploy App**: Select "New App" and point it to:
    *   **Repository**: `Matu94/YT-SF-Agentic`
    *   **Branch**: `dev` (or `prod`)
    *   **Main file path**: `streamlit/Home.py`
3.  **Configure Secrets**: Navigate to the app's Advanced Settings -> Secrets. You must inject the AWS credentials so the app can read the Parquet files:
    ```toml
    AWS_ACCESS_KEY_ID = "AKIA..."
    AWS_SECRET_ACCESS_KEY = "..."
    S3_BUCKET_NAME = "yt-sf-metrics-data-prod"
    AWS_DEFAULT_REGION = "eu-north-1"
    ```

## 5. Benefits & Capabilities
*   **Zero Compute Cost**: Community Cloud is free for public repositories.
*   **High Performance**: Reading static Parquet files into a Pandas DataFrame is blazingly fast.
*   **Instant Updates**: Committing code to the `streamlit/` folder in the GitHub branch instantly triggers a rebuild of the Community Cloud app.
*   **Data Freshness**: The data is as fresh as the last GitHub Action `export_parquet_s3.yml` run (daily at 05:00 UTC).
