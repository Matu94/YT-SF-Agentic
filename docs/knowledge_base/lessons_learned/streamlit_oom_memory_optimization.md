# Lesson Learned: Streamlit Memory Optimization & Scaling Beyond 1GB Limits

## 1. Context & Symptoms
When deploying the analytical dashboard to **Streamlit Community Cloud** (which enforces a strict **1GB container RAM limit**), users frequently encountered the generic fatal error:
```text
Oh no.
Error running app. If you need help, try the Streamlit docs and forums.
```
This error occurred when opening the **Video Statistics** page, selecting or removing multiple channels rapidly from multiselect filters, or toggling between rolling metric grains.

---

## 2. Root Cause Analysis

Even though the underlying exported `.parquet` files on S3 appeared small (~24 MB), the application crashed due to multiple compounding memory and execution bottlenecks:

### A. Eager Full-Table Ingestion
* **The Mechanism**: `load_data()` pulled the entire `RPT_VIDEO_PERFORMANCE_DAILY.parquet` file (all historical dates, all channels, all videos) into memory upfront.
* **The Problem**: User filters (selecting 1–5 channels) were evaluated *after* the entire 900,000+ row dataset was loaded into Python memory.

### B. Python Object String Memory Explosion
* **The Mechanism**: When standard Pandas deserializes a Parquet file, every text column (`VIDEO_TITLE`, `CHANNEL_TITLE`, `VIDEO_ID`, `ORGANIZATION`, `TEAM_STUDIO`) is converted into individual Python `object` string instances.
* **The Problem**: A 24 MB Parquet file with ~900,000 rows across 7 string columns generates ~6.3 million Python string objects in memory. In RAM, this expands from 24 MB on disk to **800 MB+ in memory**, instantly exhausting the 1GB container limit.

### C. Rapid UI Reruns & Concurrency Overhead
* **The Mechanism**: Streamlit re-executes the entire script from line 1 to end on every single widget change (e.g. removing channel chips one-by-one).
* **The Problem**: Rapid user clicks spawn overlapping execution threads. When heavy operations (such as global datetime re-allocations or un-cached `.groupby()` operations across 15M rows) exist at the script root, memory usage spikes exponentially before Python's garbage collector can reclaim memory.

### D. Multiple Granular Cache Bloat
* **The Mechanism**: Toggling between "Daily", "Rolling 7-Day", and "Rolling 30-Day" loaded three separate video-grain tables (`RPT_VIDEO_PERFORMANCE_DAILY`, `_ROLLING_7D`, `_ROLLING_30D`).
* **The Problem**: Streamlit cached all three large tables simultaneously in memory, causing cumulative RAM starvation.

---

## 3. Solutions & Architectural Patterns

### Solution 1: PyArrow C++ Memory Backend (`dtype_backend='pyarrow'`)
* **How it works**: Passing `engine='pyarrow'` and `dtype_backend='pyarrow'` into `pd.read_parquet()` prevents Pandas from converting strings into individual Python objects. 
* **Impact**: Strings remain contiguous Arrow C++ memory structures. RAM footprint drops from ~800 MB to ~40 MB.

### Solution 2: Lazy S3 Querying via DuckDB (Recommended for S3 Architecture)
* **How it works**: Instead of downloading the full Parquet file into Pandas, use embedded **DuckDB with `httpfs`**. DuckDB reads Parquet metadata and uses **HTTP range requests** to download *only* the specific byte ranges matching the user's selected channels and date windows:
  ```python
  import duckdb
  import streamlit as st

  con = duckdb.connect(database=':memory:')
  con.execute("INSTALL httpfs; LOAD httpfs;")
  con.execute(f"SET s3_region='{aws_region}'; SET s3_access_key_id='{aws_key}'; SET s3_secret_access_key='{aws_secret}';")

  # Only fetches rows for selected channels from S3
  query = """
      SELECT * 
      FROM read_parquet('s3://yt-sf-metrics-data-prod/mart/rpt_video_performance_daily.parquet')
      WHERE CHANNEL_TITLE = ANY($1)
        AND METRIC_DATE >= CURRENT_DATE - INTERVAL 30 DAY
  """
  df = con.execute(query, [selected_channels]).df()
  ```
* **Impact**: Zero server infrastructure costs (100% free open-source library), and Streamlit Cloud RAM consumption stays under 15 MB.

### Solution 3: Native Streamlit in Snowflake (SiS) (Best Long-term Platform Architecture)
* **How it works**: Deploy the Streamlit app directly inside Snowflake.
* **Impact**:
  * Eliminates the 1GB container ceiling entirely (even an `X-Small` virtual warehouse provides ~16 GB RAM).
  * Direct SQL pushdown (`WHERE CHANNEL_TITLE = ...`) executed in the warehouse.
  * Completely removes the need for S3 export pipelines, external storage buckets, and AWS secret management.

---

## 4. Key Takeaways & Best Practices

1. **Parquet on disk $\neq$ memory in Pandas**: Highly compressed columnar files expand up to 30x in standard Pandas due to Python object wrappers. Always leverage PyArrow dtypes for text-heavy analytical datasets.
2. **Push down filters before ingestion**: Avoid pulling full tables to filter downstream in memory. Either filter at the SQL layer (Snowflake / DuckDB HTTP range requests) or slice partitioned directories.
3. **Never mutate cached data at root level**: Parse dates and data types *inside* the `@st.cache_data` loader function so transformations execute once upon load, rather than on every rapid UI interaction.
4. **Isolate baseline aggregations**: Compute dataset-wide metadata (like channel onboarding dates) from lightweight channel-grain tables (`RPT_CHANNEL_PERFORMANCE_DAILY`) rather than scanning millions of video-grain rows.

