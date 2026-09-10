# Lesson Learned: Pushdown Aggregation vs. Pandas In-Memory Processing

## The Context
During the scaling of the YouTube Metrics Streamlit dashboard, we encountered severe latency and Out-Of-Memory (OOM) risks when interacting with the Video Statistics page. The dashboard allows users to select multiple YouTube channels and visualize video performance trends over 7 to 30 day rolling windows.

## The Anti-Pattern: Pandas `groupby()` on Big Data
Initially, the data extraction layer (`load_filtered_video_data`) was designed to execute a standard `SELECT * FROM s3_parquet` query via DuckDB. DuckDB would download the raw data over HTTP, convert the entirety of it into a Pandas DataFrame, and hand it to Streamlit.

Inside Streamlit, we used Pandas to perform aggregations for the Altair charts:
```python
df_trend_filtered.groupby(['METRIC_DATE', 'CHANNEL_TITLE']).sum()
```

### Why it failed to scale:
While Altair charting was safe (because it only received the final 120 grouped rows), the **Python Memory footprint** was unsustainable. 
* 1 Channel = 20,000 videos = 20,000 rows per day.
* 40-day window = 800,000 rows per channel.
* Selecting 5 channels forced DuckDB to download **4,000,000 rows** of raw video data into the 2GB DigitalOcean container.

This saturated the network bandwidth and maxed out the container's RAM, causing massive latency.

## The Solution: SQL Pushdown Aggregation
DuckDB is an optimized C++ analytical engine, uniquely capable of streaming aggregations over HTTP without materializing the entire dataset in RAM.

Instead of extracting raw data and grouping it in Pandas, the logic was refactored into **Pushdown Aggregations**. We rewrote the Streamlit data loaders to execute the `GROUP BY` logic natively in DuckDB SQL:

```sql
SELECT METRIC_DATE, CHANNEL_TITLE, VIDEO_TYPE, SUM(DAILY_VIEWS)
FROM read_parquet(...)
WHERE CHANNEL_TITLE IN (...)
GROUP BY METRIC_DATE, CHANNEL_TITLE, VIDEO_TYPE
```

### The Impact:
1. **Network Payload Slashed**: DuckDB only transfers the aggregated results (e.g., 120 rows) over the internet instead of 4,000,000 rows.
2. **Zero OOM Risk**: The 2GB DigitalOcean container's memory footprint dropped to almost zero, as Pandas only ever interacts with the tiny pre-calculated summary tables.
3. **Lightning Fast UI**: Streamlit no longer spends seconds parsing and grouping millions of rows, allowing Altair to render instantly.

## Key Takeaway (Kimball / Big Data Rule)
**Never use Pandas/Python to aggregate massive Fact tables.** If an aggregation can be expressed in SQL, it must be pushed down to the Database Engine (DuckDB/Snowflake). Python should only be used to render the final results.
