# ADR 016: Snowflake Native Parquet Export to AWS S3

## Status
Accepted

## Context
In **ADR-010**, we decided to decouple the Streamlit frontend from Snowflake by exporting our presentation views (`RPT_*`) to AWS S3 as Parquet files. This export was originally orchestrated via a GitHub Action (`export_parquet_s3.yml`) executing a Python script (`export_to_s3.py`).

While this approach successfully protected Snowflake compute costs from public web traffic, it introduced external dependencies (GitHub Actions and Python Pandas runtime) for a task that can be natively handled by Snowflake's engine. Moving the extraction logic into Snowflake consolidates all data transformation and egress operations under a single orchestration layer (Snowflake Tasks) and removes the need to pass massive amounts of data through an intermediate GitHub Actions runner before uploading it to S3.

## Decision
We will deprecate the GitHub Actions Python export script in favor of a **Native Snowflake Task** that uses the `COPY INTO <location>` command to push Parquet files directly to our AWS S3 bucket.

1. **Storage Integration & External Stage:** We will configure a Snowflake Storage Integration (`AWS_S3_INTEGRATION`) mapped to an IAM role, and create an External Stage pointing to the `s3://yt-sf-metrics-data-prod/mart/` prefix.
2. **Native Extraction Procedure/Task:** We will implement a Snowflake Stored Procedure (or direct SQL Task) that dynamically loops over the presentation views and executes `COPY INTO @our_s3_stage/view_name.parquet FROM view_name FILE_FORMAT = (TYPE = PARQUET) HEADER = TRUE`.
3. **Orchestration:** The native Task will be scheduled using Snowflake's built-in `SCHEDULE` engine, completely replacing the GitHub Actions cron.
4. **Clean-up:** The legacy `.github/workflows/export_parquet_s3.yml` and `.deployment/export_to_s3.py` files will be removed.

## Consequences
*   **Positive (Architecture Simplification):** All data transformations, including egress, are now unified within the Snowflake platform.
*   **Positive (Performance & Scalability):** Snowflake's native `COPY INTO` command is vastly more efficient at generating Parquet files and streaming them to S3 than an intermediate Python Pandas script running on a constrained GitHub Actions runner.
*   **Positive (Security):** AWS credentials can be managed securely via an IAM Trust Policy and Snowflake Storage Integration, eliminating the need to pass AWS access keys as GitHub Secrets.
*   **Negative (Vendor Lock-in):** Increases reliance on Snowflake-specific features (External Stages and Tasks) over generic Python automation, although this aligns with our overall architectural strategy.

## Implementation Notes (For Data Engineer)
*   Ensure the Storage Integration and External Stage DDL are idempotent and added to the appropriate setup scripts.
*   Write a robust SQL/Snowpark Task that automatically overwrites the existing Parquet files on S3 to maintain the daily update pattern required by the Streamlit dashboard.
*   Follow the standard numerical prefixing for any new DDL deployments in the `.release` flow.
