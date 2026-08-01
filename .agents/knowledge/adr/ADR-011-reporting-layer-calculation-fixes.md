# ADR 011: Reporting Layer Calculation Fixes

## Status
Accepted

## Context
During a routine data quality and query validation check of the dbt models in the `marts/presentation` and `marts/performance` layers, three significant analytical issues were identified:
1. **SCD Type 2 Fan-out Bug:** `dim_channel` was joined into rolling video reports (`rpt_video_performance_rolling_7d` and `30d`) using only the natural `channel_id`. Since `dim_channel` is an SCD Type 2 dimension, this resulted in a Cartesian product (fan-out) for any channels with historical state changes.
2. **Global Max Date Filtration Trap:** The top video leaderboards (`rpt_top_video_by_views`, `likes`, `comments`) used a global `MAX(date_id)` scalar subquery to find the latest metrics. This caused videos that failed to update on the exact global maximum date (due to API failures, pipeline hiccups, or deletion) to be completely dropped from the reports, instead of displaying their latest known metrics.
3. **Gap Vulnerability in Rolling Window Functions:** Rolling metrics (`fct_rolling_7d_video_metrics`, etc.) utilized `ROWS BETWEEN X PRECEDING AND CURRENT ROW`. This physical row counting assumes a perfectly contiguous, gapless pipeline. If a daily load is missed, the rolling window spans a larger number of calendar days than intended.

## Decision
We will implement the following corrective measures to ensure analytical accuracy:

1. **SCD Type 2 Resolution:** We will add temporal bounds to all `dim_channel` joins in the presentation layer where a surrogate key (`channel_sk`) is not already used. Joins will explicitly include:
   `AND f.date_id >= DATE(c.valid_from) AND f.date_id < COALESCE(DATE(c.valid_to), '9999-12-31'::DATE)`
2. **Robust Latest Metric Selection:** We will refactor the leaderboard models to use a Window Function (`ROW_NUMBER() OVER(PARTITION BY video_id ORDER BY date_id DESC)`) rather than a global scalar max. This guarantees every video is represented by its most recent available datapoint.
3. **Acceptance of Gap Vulnerability (For Now):** As the pipeline is currently scheduled for daily continuous runs, we will accept the risk of `ROWS BETWEEN` for the rolling window functions. Introducing a complete date-spine or refactoring to `RANGE` (which requires integer dates in Snowflake) introduces unnecessary complexity at this stage of the hobby project. We will revisit this if missing days become a frequent pipeline issue.

## Consequences
* **Positive (Accuracy):** Prevents metric duplication by resolving the SCD Type 2 fan-out issue.
* **Positive (Completeness):** Ensures the leaderboard reports remain stable and include all videos regardless of isolated extraction failures.
* **Neutral (Risk Acceptance):** The reliance on `ROWS BETWEEN` remains a known technical debt dependent on the reliability of the daily extraction schedule.
