# Lesson Learned: Streamlit Memory Optimization & Out-Of-Memory (OOM) Crashes

## Context
While deploying our dashboard to the Streamlit Community Cloud (which strictly limits container memory to 1GB), the application began crashing frequently with the generic `"Oh no. Error running app."` message, particularly when users accessed the Video Statistics page.

## Root Cause Analysis
This generic error in the Community Cloud is highly indicative of an Out-Of-Memory (OOM) event. As our data warehouse (`MART` layer) scaled to include more historical metrics and video data, the frontend was hitting the 1GB RAM ceiling. The crash was traced to two primary memory bottlenecks:

1. **Inefficient Data Loading (`data_loader.py`)**: 
   The application utilized `boto3` to pull the entire S3 Parquet file into an `io.BytesIO` memory buffer before handing it over to Pandas for parsing. This meant the container had to hold the massive compressed binary blob *and* the fully materialized Pandas DataFrame in memory at the exact same time.

2. **Redundant DataFrame Duplication (`1_Video_Statistics.py`)**:
   The frontend script explicitly duplicated the large dataset returned by the cache using deep copies (e.g., `df_full = df.copy()`) before applying sidebar hierarchy filters.

## The Solution

To ensure the dashboard remains highly performant and stable under the 1GB limit, we implemented the following fixes:

### 1. Native Pandas S3 Streaming
We refactored `data_loader.py` to bypass `boto3` and `BytesIO` altogether. By passing the native `s3://` URI directly into `pd.read_parquet()` (leveraging the `s3fs` library), the PyArrow engine can now intelligently stream the Parquet chunks directly from AWS, drastically reducing the peak memory footprint during data ingestion.

### 2. Passing by Reference
We stripped all `.copy()` calls from the Streamlit frontend. Streamlit's `@st.cache_data` already manages safe, isolated data caching. When creating subset views for user filters (e.g., Organizations, Teams), passing dataframe references rather than duplicating the entire table keeps memory overhead strictly proportional to the data displayed, rather than the data stored.

## Best Practices Going Forward
* **Avoid `.copy()` on large dimensional tables**: Only duplicate data if you are explicitly mutating the rows or columns in ways that violate cache safety. For read-only frontend slicing and filtering, stick to references.
* **Trust the underlying engines**: Allow Pandas and PyArrow to handle remote storage natively instead of forcing everything into intermediate memory buffers.
