# ADR 010: Streamlit Presentation Layer Static Export to AWS S3

## Status
Accepted

## Context
Our presentation layer leverages Streamlit to visualize the One Big Table (OBT) views (`RPT_VIDEO_PERFORMANCE_DAILY`, etc.) built via dbt on Snowflake. The requirement is to share this Streamlit application publicly using Streamlit Community Cloud.

However, our infrastructure relies on strict compute isolation and budget constraints (15 Credits/month). Allowing a publicly accessible Streamlit app to connect directly to Snowflake would result in unpredictable warehouse wake-ups and immediate compute cost accumulation upon every user interaction, breaking our cost-management guarantees.

## Decision
We will decouple the Streamlit Community Cloud frontend from the Snowflake data warehouse entirely at runtime.

1.  **Static Data Export:** We will introduce a scheduled data extraction process. A Python script running in our CI/CD environment (GitHub Actions) will connect to Snowflake once daily, query the required presentation views, and extract the data into compressed Parquet files.
2.  **AWS S3 Storage:** The extracted Parquet files will be uploaded directly to an Amazon S3 bucket.
3.  **App Architecture:** The Streamlit application hosted on Streamlit Community Cloud will be configured to read these Parquet files directly from the AWS S3 bucket (using Pandas/Polars or DuckDB in-memory) instead of querying Snowflake.

## Consequences
*   **Positive (Cost Control):** Guarantees zero Snowflake compute costs from public user interactions. The only compute utilized is the single daily extraction job.
*   **Positive (Security):** No Snowflake credentials need to be stored in the Streamlit Community Cloud environment.
*   **Negative/Neutral (Data Freshness):** The public dashboard will only show data as fresh as the last scheduled GitHub Actions run (e.g., updated once daily), sacrificing real-time updates for cost safety.
*   **Neutral (Infrastructure):** Requires provisioning and managing an AWS S3 bucket and injecting AWS credentials into both the GitHub Actions workflow and the Streamlit Community Cloud secrets.
