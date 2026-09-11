# ADR-012: Past 7-Day & 30-Day Daily Video Reporting and Leaderboard KPI Enhancements

## Status
Proposed

## Context
During user experience evaluation of the Streamlit analytics interface, three key usability and analytical challenges were identified:

1. **Daily vs. Rolling Metric Ambiguity:** On the Video Statistics page (`2_Video_Statistics.py`), switching between "Daily", "Weekly", and "Monthly" toggled between a single-day snapshot of yesterday's performance and 7-day/30-day *rolling sums* (`ROLLING_7D_VIEWS`, `ROLLING_30D_VIEWS`). Users lacked a discrete day-by-day daily view trend across a 7-day or 30-day window, leading to confusion between daily deltas and rolling cumulative aggregates.
2. **Missing Explanatory Context:** The UI lacked inline documentation and math formulas explaining how daily deltas ($\Delta \text{Views}$) differ from rolling window totals ($\sum_{i=t-N+1}^t \Delta \text{Views}_i$).
3. **Leaderboard Network Scope Gap:** The Leaderboard page (`3_Leaderboard.py`) focused strictly on top individual video rankings but omitted high-level network/channel aggregate metrics (Total Subscribers, Total Views, Total Videos).
4. **Presentation Layer Filter Limitation:** The presentation views `MART.RPT_VIDEO_PERFORMANCE_DAILY` and `MART.RPT_CHANNEL_PERFORMANCE_DAILY` enforced a single-day strict equality filter (`WHERE f.date_id = DATEADD(day, -1, CURRENT_DATE())`), preventing Streamlit from querying daily history across multiple days from these unified views.

## Decision

We will implement the following changes across the presentation layer and Streamlit user interface:

### 1. Presentation Layer Refactoring (`dbt/models/marts/presentation/`)
- Update `rpt_video_performance_daily.sql` and `rpt_channel_performance_daily.sql` to replace the strict single-day equality filter with an upper-bound constraint:
  `WHERE f.date_id <= DATEADD(day, -1, CURRENT_DATE())`
- This exposes historical daily records up to yesterday, allowing Streamlit to perform single-day, past 7-day daily, and past 30-day daily trend queries without adding duplicate tables.

### 2. Downstream Duplication & SCD Type 2 Safety Analysis
We conducted a formal audit to verify that removing the single-day equality filter does NOT introduce data duplication or fan-out in downstream consumption:
- **Presentation Model Join Integrity:**
  - `rpt_video_performance_daily`: Joins `fct_daily_video_metrics` (grain: `video_id` + `date_id`) to `dim_channel` using strict temporal bounds (`f.date_id >= DATE(d.valid_from) AND f.date_id < COALESCE(DATE(d.valid_to), '9999-12-31'::DATE)`). Because SCD Type 2 time ranges are strictly non-overlapping, every `video_id` + `date_id` pair matches exactly 1 dimension state. Grain is guaranteed at 1 row per `video_id` per `date_id`.
  - `rpt_channel_performance_daily`: Joins `fct_daily_channel_metrics` to `dim_channel` on surrogate key `f.channel_sk = d.channel_sk`. Grain is guaranteed at 1 row per `channel_id` per `date_id`.
- **Streamlit Downstream Aggregation Rules:**
  - **Single-day views (`Home.py`, `Channel_Info.py`, Leaderboard KPIs, Yesterday Snapshot):** Filter using `METRIC_DATE == MAX(METRIC_DATE)`. Exactly 1 row per entity is returned for that date, ensuring subscriber, view, and video sums are 100% accurate without double-counting.
  - **Multi-day daily trends (`Video_Statistics.py`):** Filter using `METRIC_DATE >= latest_date - N days`. Groupings by date (trend chart) or video ID (period total sum) cleanly accumulate discrete daily view deltas without duplication.
- **dbt DAG End-Node Verification:** `RPT_VIDEO_PERFORMANCE_DAILY` and `RPT_CHANNEL_PERFORMANCE_DAILY` are final presentation views with zero downstream dbt model dependencies.

### 3. Video Statistics UI Refactoring (`streamlit/pages/2_Video_Statistics.py`)
- Restructure the report mode options into explicit, unambiguous options:
  - **Daily - Yesterday Snapshot:** Metrics for the single most recent complete day.
  - **Daily - Past 7 Days Trend:** Day-by-day discrete view gain breakdown over the last 7 calendar days.
  - **Daily - Past 30 Days Trend:** Day-by-day discrete view gain breakdown over the last 30 calendar days.
  - **Rolling 7-Day Trend:** Trailing 7-day cumulative sum of views evaluated daily.
  - **Rolling 30-Day Trend:** Trailing 30-day cumulative sum of views evaluated daily.
- Add an interactive inline explanation callout / expander detailing calculation logic:
  - $\text{Daily Delta Views} = \text{Total Views}_{\text{today}} - \text{Total Views}_{\text{yesterday}}$
  - $\text{Rolling Views}(t) = \sum_{i=t-N+1}^t \text{Daily Views}_i$

### 4. Leaderboard Page Enhancements (`streamlit/pages/3_Leaderboard.py`)
- Add high-level network KPI cards at the top of the Leaderboard page:
  - 👥 **Total Subscribers**
  - 👀 **Total Views**
  - 📹 **Total Videos**
- Ensure KPI metrics dynamically respond to hierarchy sidebar filters (Organization, Channel).

## Consequences

* **Positive (Usability & Clarity):** Resolves metric confusion by giving users both discrete daily breakdown trends and rolling aggregate views alongside explicit explanations.
* **Positive (Network Overview):** Provides instant high-level context on network size and reach directly on the Leaderboard page.
* **Positive (Data Model Efficiency):** Avoids table proliferation by allowing `RPT_VIDEO_PERFORMANCE_DAILY` to serve both single-day snapshots and historical daily trends.
* **Positive (Verified Non-Duplication):** Confirmed mathematically and dimensionally that no fan-out or double-counting occurs.
* **Neutral (dbt View Update):** Requires redeploying presentation views to Snowflake.
