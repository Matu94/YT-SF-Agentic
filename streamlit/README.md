# Snowflake Native Streamlit Application

This directory contains the Python source code and environment configuration for the **YouTube Metrics Dashboard**, hosted natively in Snowflake as a multi-page Streamlit application.

## 🏗️ Architecture & Data Sourcing

Following Kimball dimensional modeling principles, the application **only queries presentation objects in the `MART` layer**. It never queries `RAW` or `LANDING` directly.

- **`MART.RPT_CHANNEL_PERFORMANCE_DAILY`**: Source for channel-level metrics, subscriber growth, and channel hierarchy.
- **`MART.RPT_VIDEO_PERFORMANCE_DAILY`**: Source for video-level metrics (views, likes, comments, video classification type).

---

## 📱 Page Structure

### 1. `Home.py` — Welcome Landing Page
- **User Authentication Context**: Dynamically retrieves the active user's Snowflake identity (`SELECT CURRENT_USER()`) to present a personalized welcome message.
- **System Status**: Displays a health indicator with the latest available metric date in the data warehouse.
- **Platform KPIs**: Displays top-level metrics (`st.metric`) for total tracked channels, total subscribers, and cumulative views across all tracked entities for the latest available date.
- **Channel Directory**: Renders an expandable (`st.expander`) directory listing all channels grouped hierarchically by **Organization** and **Team/Studio**.

### 2. `pages/1_Daily_Views.py` — Daily Channel Views Dashboard
- **Hierarchy Filters**: Single-select dropdown filters for Organization, Studio, and Channel.
- **Performance Charting**: Altair bar chart displaying daily view performance per channel.

### 3. `pages/2_Video_Statistics.py` — Video Statistics Dashboard
- **Metric Grain Toggle**: UI toggle for switching between *Daily* and *Weekly* metrics (Weekly currently framed as a placeholder).
- **Date Filtering**: Automatically filters to the latest `METRIC_DATE` to present single-day performance.
- **Cascading Multi-Select Filters**: Independent multi-select filters for:
  - **Organizations**: Filter channels across multiple networks.
  - **Teams (Studios)**: Cascades dynamically based on selected Organizations.
  - **Channels**: Cascades dynamically based on selected Teams.
- **Content Format Filter**: Multi-select filter for `VIDEO_TYPE` (`video`, `short`, `live`).
- **Aggregated Channel Chart**: Altair bar chart showing views per channel with rich tooltip metrics (Channel Name, Period Views, and `VIDEO_COUNT` indicating how many videos contributed to those views).
- **Top Videos Table**: Data table displaying the top 100 performing videos for the selected day, featuring direct YouTube watch links rendered via `st.column_config.LinkColumn`.

---

## ⚙️ Dependencies & Deployment

Dependencies are defined in `environment.yml`:
- `python=3.11`
- `streamlit`
- `snowflake-snowpark-python`
- `altair`
- `pandas`

Deployment to Snowflake Native Streamlit is automated via DDL script `snowflake/04_mart/08_streamlit/01_youtube_metrics_dashboard.sql` which points to `MART.STREAMLIT_STAGE`.
