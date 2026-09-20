# ADR 017: Restoring Hive Partitioning for Snowflake S3 Parquet Exports

## Status
Accepted

## Context
In **ADR 016**, we migrated our data export pipeline from a GitHub Actions Python script (`export_to_s3.py`) to a Native Snowflake Task (`MART.EXPORT_MART_TO_S3`). The goal was to consolidate data transformations and egress operations within Snowflake for better performance and simplicity.

However, the Python script we deprecated was responsible for partitioning large video reporting tables (like `RPT_VIDEO_PERFORMANCE_DAILY`) into Hive-partitioned folders by `CHANNEL_TITLE` (e.g., `CHANNEL_TITLE=Partizan/`). This partitioning was critical for the Streamlit app's DuckDB backend to perform fast, targeted network lookups without downloading massive monolithic files—an optimization that previously solved a severe 504 Gateway Timeout issue (as documented in our lessons learned).

The newly implemented Snowflake Stored Procedure utilized the `COPY INTO` command with the `SINGLE = TRUE` flag, producing a single monolithic `.parquet` file for every view. As a result, the Streamlit app's Video Statistics page continued reading from the old, now-stale partitioned folders, while the Snowflake task blindly updated the unused monolithic files.

## Decision
We will modify the Snowflake Stored Procedure (`MART.EXPORT_MART_TO_S3`) to natively output Hive-partitioned folders for the large video tables, restoring the partitioning strategy required by the Streamlit frontend.

1. **Conditional Export Logic**: We will update the Stored Procedure to differentiate between "Channel" views (which are small enough to remain monolithic) and "Video" views (which require partitioning).
2. **Remove SINGLE = TRUE**: For views requiring partitioning (e.g., `RPT_VIDEO_%`), we will remove the `SINGLE = TRUE` flag in the `COPY INTO` command, as it forces a single file and is incompatible with partitioned output.
3. **Implement PARTITION BY**: We will add a `PARTITION BY ( 'CHANNEL_TITLE=' || CHANNEL_TITLE )` clause to the `COPY INTO` statement for the large video views. This instructs Snowflake to dynamically create folders on the S3 stage formatted identically to our PyArrow partitions (`CHANNEL_TITLE=.../data.parquet`).

## Consequences
*   **Positive (Data Integrity)**: The Streamlit app will once again serve fresh, up-to-date data on the Video Statistics page.
*   **Positive (Performance)**: We maintain the DuckDB network predicate pushdown optimization, keeping dashboard load times in the milliseconds and avoiding 504 Gateway Timeouts.
*   **Positive (Simplicity)**: We fully achieve the goal of ADR 016 (native Snowflake orchestration) without sacrificing the advanced Hive partitioning capabilities previously provided by Python and PyArrow.
*   **Negative (Complexity)**: The Snowflake Stored Procedure will become slightly more complex, requiring conditional logic to handle partitioned vs. non-partitioned exports dynamically based on the view name.
