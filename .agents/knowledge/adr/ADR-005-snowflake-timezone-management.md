# ADR-005: Snowflake Timezone Management

## 1. Context & Problem Statement
Currently, the YouTube Metrics Pipeline extracts data using the `Europe/Budapest` timezone. This is correctly enforced in the data extraction phase:
*   The Snowflake Native Task (`LOAD_YOUTUBE_API_DATA_TASK`) is scheduled using `CRON 0 0 * * * Europe/Budapest`.
*   The Snowpark Stored Procedure (`EXTRACT_YOUTUBE_METRICS_SP`) explicitly sets the session timezone (`ALTER SESSION SET TIMEZONE = 'Europe/Budapest'`).

**The Bug:**
Snowflake's default account-level `TIMEZONE` parameter is set to `America/Los_Angeles` (UTC-8). Because of the 9-hour offset, when a user in Budapest executes `SELECT CURRENT_DATE()` before 09:00 AM local time, Snowflake evaluates the date as "yesterday" (since it is still before midnight in Los Angeles).

This timezone discrepancy breaks the presentation layer models (e.g., `rpt_channel_performance_daily` and `rpt_video_performance_daily`), which rely on `CURRENT_DATE()` to filter for the latest metrics:
```sql
WHERE f.date_id = DATEADD(day, -1, CURRENT_DATE())
```
During the morning in Budapest, `CURRENT_DATE()` evaluates to yesterday, causing the `DATEADD` function to filter for the *day before yesterday*, resulting in stale or missing data in the Streamlit dashboard.

## 2. Decision & Recommendations

To guarantee deterministic, timezone-aware execution across all layers (Extract, Transform, Presentation, and Ad-Hoc queries), we must explicitly configure the timezone at the infrastructure layer, rather than relying on session-level or query-level conversions.

### Action Items for the User (Source Code Modifications):

1.  **Account-Level / User-Level Configuration (Recommended Approach):**
    You must set the default timezone to `Europe/Budapest` globally or for the specific users (e.g., the dbt user and your personal user). 
    Update the initialization script (`.setup/snowflake/00_infrastructure_init.sql` or `03_user_init.sql`) by adding:
    ```sql
    ALTER ACCOUNT SET TIMEZONE = 'Europe/Budapest';
    -- OR at the user level:
    ALTER USER <your_user> SET TIMEZONE = 'Europe/Budapest';
    ALTER USER <dbt_user> SET TIMEZONE = 'Europe/Budapest';
    ```
    *Note: Account-level parameter change requires the `ACCOUNTADMIN` role.*

2.  **Robust dbt Modeling (Alternative/Failsafe Approach):**
    If account-level modifications are not preferred, update the dbt presentation models to perform explicit timezone conversions. Replace `CURRENT_DATE()` with a timezone-aware cast:
    ```sql
    -- In rpt_channel_performance_daily.sql and rpt_video_performance_daily.sql
    WHERE f.date_id = DATEADD(day, -1, CONVERT_TIMEZONE('Europe/Budapest', CURRENT_TIMESTAMP())::DATE)
    ```

## 3. Consequences
By implementing the account/user-level `TIMEZONE` parameter:
*   **Pros:** Ad-hoc queries running `CURRENT_DATE()` will logically match the user's local time in Budapest. Dbt models relying on `CURRENT_DATE()` will automatically evaluate correctly without complex timezone logic.
*   **Cons:** Any legacy jobs relying on the implicit `America/Los_Angeles` default (if they exist outside this project scope) might be impacted if applied at the account level.

*As the Principal Data Architect, I advise implementing the Account-Level `TIMEZONE` parameter to ensure a single source of truth for time across the entire data warehouse.*
