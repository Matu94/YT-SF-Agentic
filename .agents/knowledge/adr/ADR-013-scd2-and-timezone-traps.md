# ADR 013: SCD Type 2 Late-Arriving Dimension and Timezone Misalignment Fixes

## Status
Accepted

## Context
During operations, a critical issue was observed in the OBT (One Big Table) presentation layer (`rpt_channel_performance_daily`, `rpt_video_performance_daily`, etc.). While the `MART` layer fact tables refreshed properly, the downstream reporting views occasionally displayed data from two days ago and dropped all newly onboarded channels, displaying only legacy channels. 

Root cause analysis identified two intersecting architectural edge cases:

1. **Session Timezone Misalignment:** The presentation layer filters for historical data using `WHERE date_id <= DATEADD(day, -1, CURRENT_DATE())`. Because `CURRENT_DATE()` evaluates dynamically at query time using the Snowflake session's default timezone (often `America/Los_Angeles`), querying the view from a European timezone early in the morning causes `CURRENT_DATE()` to evaluate to "yesterday." This effectively forces the upper-bound filter to restrict data to "the day before yesterday" (`T-2`), hiding the newly loaded `T-1` pipeline facts.
2. **SCD Type 2 Late-Arriving Dimension Trap:** The PRD requires full historical payload extraction for newly onboarded channels. However, when these channels are processed into `dim_channel`, their initial dimension record receives a `valid_from` timestamp equal to the current load time (e.g., today). Because the reporting layer employs an INNER JOIN to resolve SCD Type 2 state (`f.date_id >= DATE(d.valid_from)`), the historical facts for new channels (which have `date_id`s from yesterday and older) fail the join condition (`Yesterday >= Today` is FALSE). This silently drops all historical facts for newly added channels from the presentation layer.

## Decision
We will implement the following architectural modifications to the pipeline's logical model:

1. **Timezone Anchoring:** We will replace the dynamic `CURRENT_DATE()` session variable in the presentation layer views with an explicit, hardcoded timezone cast. The freshness bound will be standardized to the pipeline's operational timezone (e.g., `CONVERT_TIMEZONE('UTC', 'Europe/Budapest', CURRENT_TIMESTAMP())::DATE`).
2. **Backdating Initial Dimensions:** We will modify the dbt dimension logic (or snapshot configuration) so that a channel's very first record in `dim_channel` does not receive `CURRENT_TIMESTAMP()` for its `valid_from`. Instead, the initial `valid_from` will be backdated to a safe epoch (e.g., `'1970-01-01'`) or the channel's actual `published_at` date. 

## Consequences
* **Positive (Accuracy & Freshness):** Ensures the reporting layer always displays the latest available `T-1` data, regardless of the BI tool or session timezone executing the query.
* **Positive (Completeness):** Ensures that full historical payload extractions for newly onboarded channels successfully map to their parent dimension records and populate the presentation layer immediately.
* **Negative (Complexity):** Introduces slightly more complex manual handling for dimension temporal boundaries and timezone casts in the dbt presentation models.
