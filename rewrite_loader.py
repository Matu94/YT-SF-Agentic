import sys

with open("streamlit/utils/data_loader.py", "r") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith("@st.cache_data"):
        if "def load_filtered_video_data" in lines[i+1]:
            start_idx = i
    if "def get_top_n_channels_from_video" in line and start_idx != -1:
        end_idx = i - 1
        break

if start_idx == -1 or end_idx == -1:
    print("Failed to find bounds.")
    sys.exit(1)

new_funcs = """@st.cache_data(ttl=3600, max_entries=2)
def load_video_trend_agg(table_name: str, selected_channels: list, days_back: int = 40) -> pd.DataFrame:
    if not selected_channels: return pd.DataFrame()
    table_name = table_name.upper()
    metric_col = "DAILY_VIEWS"
    if "7D" in table_name: metric_col = "ROLLING_7D_VIEWS"
    elif "30D" in table_name: metric_col = "ROLLING_30D_VIEWS"
    
    channels_str = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in selected_channels])
    
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        query = f"SELECT METRIC_DATE, CHANNEL_TITLE, VIDEO_TYPE, SUM({metric_col}) as {metric_col} FROM MART.{table_name} WHERE CHANNEL_TITLE IN ({channels_str}) AND METRIC_DATE >= DATEADD(day, -{days_back}, CURRENT_DATE()) GROUP BY METRIC_DATE, CHANNEL_TITLE, VIDEO_TYPE"
        df = session.sql(query).to_pandas()
        if 'METRIC_DATE' in df.columns: df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
        return df
    except Exception:
        pass

    con = get_duckdb_connection()
    import os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    local_path = os.path.join(project_root, "data", "export", f"{table_name.lower()}.parquet")
    
    if os.path.exists(local_path):
        if os.path.isdir(local_path):
            import urllib.parse
            exact_paths = [f"{local_path}/CHANNEL_TITLE={urllib.parse.quote(c)}/*.parquet" for c in selected_channels]
            target_path_sql = "[" + ", ".join([f"'{p}'" for p in exact_paths]) + "]"
        else:
            target_path_sql = f"'{local_path}'"
    else:
        bucket_name = _get_config("S3_BUCKET_NAME", "yt-sf-metrics-data-prod")
        aws_key = _get_config("AWS_ACCESS_KEY_ID")
        aws_secret = _get_config("AWS_SECRET_ACCESS_KEY")
        aws_region = _get_config("AWS_DEFAULT_REGION", "eu-north-1")
        if aws_key and aws_secret:
            con.execute(f"SET s3_region='{aws_region}'; SET s3_access_key_id='{aws_key}'; SET s3_secret_access_key='{aws_secret}';")
        import urllib.parse
        exact_paths = [f"s3://{bucket_name}/mart/{table_name.lower()}.parquet/CHANNEL_TITLE={urllib.parse.quote(c)}/*.parquet" for c in selected_channels]
        target_path_sql = "[" + ", ".join([f"'{p}'" for p in exact_paths]) + "]"
            
    query = f"SELECT METRIC_DATE, CHANNEL_TITLE, VIDEO_TYPE, SUM({metric_col}) as {metric_col} FROM read_parquet({target_path_sql}, hive_partitioning=1) WHERE CHANNEL_TITLE IN ({channels_str}) AND METRIC_DATE >= CURRENT_DATE() - INTERVAL {days_back} DAY GROUP BY METRIC_DATE, CHANNEL_TITLE, VIDEO_TYPE"
    df = con.execute(query).df()
    if 'METRIC_DATE' in df.columns: df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
    return df

@st.cache_data(ttl=3600, max_entries=2)
def load_video_snapshot_top(table_name: str, selected_channels: list) -> pd.DataFrame:
    if not selected_channels: return pd.DataFrame()
    table_name = table_name.upper()
    channels_str = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in selected_channels])
    
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        query = f"SELECT * FROM MART.{table_name} WHERE CHANNEL_TITLE IN ({channels_str}) AND METRIC_DATE = (SELECT MAX(METRIC_DATE) FROM MART.{table_name} WHERE CHANNEL_TITLE IN ({channels_str}))"
        df = session.sql(query).to_pandas()
        if 'METRIC_DATE' in df.columns: df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
        return df
    except Exception:
        pass

    con = get_duckdb_connection()
    import os
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    local_path = os.path.join(project_root, "data", "export", f"{table_name.lower()}.parquet")
    
    if os.path.exists(local_path):
        if os.path.isdir(local_path):
            import urllib.parse
            exact_paths = [f"{local_path}/CHANNEL_TITLE={urllib.parse.quote(c)}/*.parquet" for c in selected_channels]
            target_path_sql = "[" + ", ".join([f"'{p}'" for p in exact_paths]) + "]"
        else:
            target_path_sql = f"'{local_path}'"
    else:
        bucket_name = _get_config("S3_BUCKET_NAME", "yt-sf-metrics-data-prod")
        import urllib.parse
        exact_paths = [f"s3://{bucket_name}/mart/{table_name.lower()}.parquet/CHANNEL_TITLE={urllib.parse.quote(c)}/*.parquet" for c in selected_channels]
        target_path_sql = "[" + ", ".join([f"'{p}'" for p in exact_paths]) + "]"
            
    query = f"SELECT * FROM read_parquet({target_path_sql}, hive_partitioning=1) WHERE CHANNEL_TITLE IN ({channels_str}) AND METRIC_DATE = (SELECT MAX(METRIC_DATE) FROM read_parquet({target_path_sql}, hive_partitioning=1) WHERE CHANNEL_TITLE IN ({channels_str}))"
    df = con.execute(query).df()
    if 'METRIC_DATE' in df.columns: df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
    return df

"""

new_lines = lines[:start_idx] + [new_funcs] + lines[end_idx:]

with open("streamlit/utils/data_loader.py", "w") as f:
    f.writelines(new_lines)

print("data_loader updated.")
