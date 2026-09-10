# Lesson Learned: S3 Parquet Partitioning & DuckDB Network Latency

## 1. Context & Symptoms
After successfully migrating our Streamlit presentation layer from Streamlit Community Cloud to **DigitalOcean App Platform** (to secure a 2GB RAM container and solve OOM crashes), we encountered a new issue:

When navigating to the **Video Statistics** page, the application would spin for 60 seconds and fatally crash with a:
`Connection error: Connection failed with status 504 (Gateway Timeout)`

## 2. Root Cause Analysis
The 504 Timeout was not an Out of Memory error, but a **Network Latency Bottleneck**. 

The DigitalOcean load balancer strictly severs HTTP connections that take longer than 60 seconds to respond. Our Python backend was exceeding this timeout limit due to two architectural flaws:

### A. The Ghost of Option C (Memory Starvation)
To survive the 1GB limit on Streamlit Community Cloud, we had previously hardcoded `con.execute("SET memory_limit='128MB';")` into DuckDB. On the new 2GB DigitalOcean container, this artificial choke starved DuckDB. When it tried to process network streams, it was forced to "spill to disk" (read/write temporary swap files). Disk I/O on a basic container is exceptionally slow, compounding the latency.

### B. The Monolithic Parquet Anti-Pattern
Our Snowflake export pipeline (`export_to_s3.py`) was dumping `RPT_VIDEO_PERFORMANCE_DAILY` as a single, monolithic `.parquet` file. 
When the user queried 5 channels out of 100, DuckDB's `httpfs` extension had to read the footer and perform massive HTTP Range Requests across the public internet (from DigitalOcean to AWS `eu-north-1`) to scan out the irrelevant channels.

## 3. The Resolution
We implemented a two-phased architectural fix focusing on **Big Data Hive Partitioning**.

### Phase 1: Unleashing RAM
We removed the aggressive 128MB memory limit in `streamlit/utils/data_loader.py`, resetting it to `1GB`. This allowed DuckDB to process the HTTP range requests entirely in RAM without touching the slow container disk.

### Phase 2: Hive Partitioning by Channel
We modified the Python export script to partition the monolithic file into a directory structure organized by `CHANNEL_TITLE`.

**Before (Monolithic):**
`s3://bucket/mart/rpt_video_performance_daily.parquet` (25MB file)

**After (Partitioned):**
```text
s3://bucket/mart/rpt_video_performance_daily.parquet/
  ├── CHANNEL_TITLE=Partizan/
  │    └── data.parquet (50 KB)
  ├── CHANNEL_TITLE=Telex.hu/
  │    └── data.parquet (50 KB)
```

**Code Changes:**
In `.deployment/export_to_s3.py`, we updated the PyArrow engine:
```python
df.to_parquet(
    s3_path, 
    engine="pyarrow",
    partition_cols=["CHANNEL_TITLE"]
)
```

In `streamlit/utils/data_loader.py`, we instructed DuckDB to recognize the Hive partitions:
```sql
SELECT * 
FROM read_parquet('s3://bucket/mart/rpt_video_performance_daily.parquet/**/*.parquet', hive_partitioning=1)
WHERE CHANNEL_TITLE IN ('Partizan', 'Telex.hu')
```

## 4. The Result
By combining Hive Partitioning with DuckDB's Predicate Pushdown, DuckDB no longer scans the entire dataset over the internet. When a user requests 5 channels, DuckDB immediately resolves the folder paths and downloads only those 5 specific tiny files. Network payload dropped by 95%, reducing the load time to milliseconds and permanently eliminating the 504 Gateway Timeout.
