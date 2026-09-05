# Snowflake Native Streamlit Application

This directory contains the Python source code and environment configuration for the **YouTube Metrics Dashboard**, hosted natively in Snowflake as a multi-page Streamlit application.

## 🏗️ Architecture & Data Sourcing

Following Kimball dimensional modeling principles and **ADR-010**, the application **only queries presentation objects in the `MART` layer**.

Data loading is fully abstracted via `streamlit/utils/data_loader.py`:
- **Dual Sourcing Mode**:
  1. **Streamlit in Snowflake (SiS)**: Automatically detects active Snowflake session (`get_active_session()`) and queries live views in Snowflake `MART`.
  2. **Streamlit Community Cloud / Local Static Mode**: Falls back to reading exported Parquet files directly from **AWS S3** (`s3://<bucket_name>/mart/<view_name>.parquet`) or local dev exports without needing Snowflake credentials or compute.

- **Presentation Views Used**:
  - `MART.RPT_CHANNEL_PERFORMANCE_DAILY`
  - `MART.RPT_VIDEO_PERFORMANCE_DAILY`
  - `MART.RPT_VIDEO_PERFORMANCE_ROLLING_7D`
  - `MART.RPT_VIDEO_PERFORMANCE_ROLLING_30D`
  - `MART.RPT_TOP_VIDEO_BY_VIEWS`
  - `MART.RPT_TOP_VIDEO_BY_LIKES`
  - `MART.RPT_TOP_VIDEO_BY_COMMENTS`

---

## 📱 Page Structure

### 1. `Home.py` — Welcome Landing Page
- **User Authentication & Developer Profile**: Dynamically retrieves active Snowflake user identity if available in SiS mode, or defaults to a clean public welcome. Integrates developer contact links (LinkedIn & GitHub) in the header subtext and sidebar.
- **System Status**: Displays a health indicator with the latest available metric date.
- **Platform KPIs**: Displays top-level metrics (`st.metric`) for total tracked channels, total subscribers, and cumulative views across all tracked entities for the latest available date.
- **Channel Directory**: Renders an expandable (`st.expander`) directory listing all channels grouped hierarchically by **Organization** and **Team/Studio**.

### 2. `pages/1_Channel_Info.py` — Channel Information Dashboard
- **Channel Selection**: Single-select dropdown for inspecting current organization, studio, content type, subscribers, views, and videos.

### 3. `pages/2_Video_Statistics.py` — Video Statistics Dashboard
- **Metric Grain Toggle**: UI toggle for switching between Daily, Rolling 7-day, and Rolling 30-day metrics.
- **Cascading Multi-Select Filters**: Independent multi-select filters for Organizations, Teams (Studios), Channels, and Video Types.
- **Aggregated Channel Chart**: Altair charts for discrete and rolling trends.
- **Top Videos Table**: Data table displaying top performing videos with YouTube watch links.

### 4. `pages/3_Leaderboard.py` — Leaderboards Dashboard
- **Video & Channel Rankings**: Displays Top 3 medal KPIs, Top 10 Altair bar charts, and Top 50 progress data grids for views, likes, comments, subscribers, and video count.

---

## ⚙️ Dependencies & Deployment

- **Streamlit in Snowflake (SiS)**: Uses `environment.yml` (snowflake, streamlit, pandas, altair).
- **Streamlit Community Cloud**: Uses `requirements.txt` (streamlit, pandas, altair, pyarrow, fastparquet, s3fs).

