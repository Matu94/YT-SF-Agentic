import os
import gc
import pandas as pd
import streamlit as st

def _get_config(key: str, default: str | None = None) -> str | None:
    val = None
    try:
        if key in st.secrets:
            val = str(st.secrets[key])
    except Exception:
        pass
    if val is None:
        val = os.getenv(key, default)
    return val.strip() if val is not None else None

@st.cache_data(ttl=3600, max_entries=2)
def load_data(table_name: str) -> pd.DataFrame:
    """
    Unified Data Loader for Streamlit.
    Detects if running inside Snowflake (SiS) or DigitalOcean App Platform (S3/Parquet).
    
    Order of Evaluation:
    1. Active Snowflake Session (Streamlit in Snowflake - SiS)
    2. Local Parquet export file (for offline local development)
    3. AWS S3 Parquet file (DigitalOcean App Platform static mode)
    """
    table_name = table_name.upper()

    # 1. Attempt Streamlit in Snowflake (SiS) active session
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        try:
            session.use_warehouse('YT_SF_REPORTING_WH')
        except Exception:
            pass  # Warehouse configuration may be managed by session role/policy
        query = f"SELECT * FROM MART.{table_name}"
        if "VIDEO_PERFORMANCE" in table_name:
            query += " WHERE METRIC_DATE >= DATEADD(day, -40, CURRENT_DATE())"
        
        df = session.sql(query).to_pandas()
        if 'METRIC_DATE' in df.columns:
            df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
        return df
    except Exception:
        pass  # Not executing inside a Snowflake-hosted Streamlit container

    # 2. Attempt local Parquet fallback (useful for local dev/testing without network)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    local_path = os.path.join(project_root, "data", "export", f"{table_name.lower()}.parquet")
    if os.path.exists(local_path):
        df = pd.read_parquet(
            local_path,
            engine="pyarrow",
            dtype_backend="pyarrow"
        )
        if 'METRIC_DATE' in df.columns:
            df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
            if "VIDEO_PERFORMANCE" in table_name:
                max_date = df['METRIC_DATE'].max()
                df = df[df['METRIC_DATE'] >= (max_date - pd.Timedelta(days=40))]
                df = df.reset_index(drop=True).copy()
        return df


    # 3. Read from S3 bucket (DigitalOcean App Platform)
    bucket_name = _get_config("S3_BUCKET_NAME", "yt-sf-metrics-data-prod")
    aws_key = _get_config("AWS_ACCESS_KEY_ID")
    aws_secret = _get_config("AWS_SECRET_ACCESS_KEY")
    aws_region = _get_config("AWS_DEFAULT_REGION", "eu-north-1")
    s3_key = f"mart/{table_name.lower()}.parquet"

    # Read via pandas native s3:// support to avoid loading entire file into memory as bytes
    storage_options = {}
    if aws_key and aws_secret:
        storage_options = {
            "key": aws_key,
            "secret": aws_secret,
            "client_kwargs": {"region_name": aws_region}
        }
    s3_path = f"s3://{bucket_name}/{s3_key}"
    
    try:
        df = pd.read_parquet(
            s3_path, 
            storage_options=storage_options if storage_options else None,
            engine="pyarrow",
            dtype_backend="pyarrow"
        )
        if 'METRIC_DATE' in df.columns:
            df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
            if "VIDEO_PERFORMANCE" in table_name:
                max_date = df['METRIC_DATE'].max()
                df = df[df['METRIC_DATE'] >= (max_date - pd.Timedelta(days=40))]
                df = df.reset_index(drop=True).copy()
        return df
    except Exception as e:
        raise RuntimeError(
            f"Failed to fetch '{s3_path}' from S3 (region: {aws_region}). "
            f"Details: {e}"
        ) from e


def get_current_user_name() -> str | None:
    """
    Helper to fetch the active Snowflake user name if running in SiS,
    or return None when running in static mode.
    """
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        current_user_row = session.sql("SELECT CURRENT_USER()").collect()
        return current_user_row[0][0]
    except Exception:
        return None

@st.cache_resource
def get_duckdb_connection():
    import duckdb
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET enable_http_metadata_cache=true;")
    con.execute("SET enable_object_cache=true;")
    return con

@st.cache_data(ttl=3600, max_entries=2)
def load_video_trend_agg(table_name: str, selected_channels: list, days_back: int = 40) -> pd.DataFrame:
    if not selected_channels: return pd.DataFrame()
    table_name = table_name.upper()
    metric_col = "DAILY_VIEWS"
    has_video_type = True
    if "7D" in table_name: 
        metric_col = "ROLLING_7D_VIEWS"
        has_video_type = False
    elif "30D" in table_name: 
        metric_col = "ROLLING_30D_VIEWS"
        has_video_type = False
        
    vt_select = ", VIDEO_TYPE" if has_video_type else ""
    vt_group = ", VIDEO_TYPE" if has_video_type else ""
    
    channels_str = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in selected_channels])
    
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        query = f"SELECT METRIC_DATE, CHANNEL_TITLE{vt_select}, SUM({metric_col}) as {metric_col} FROM MART.{table_name} WHERE CHANNEL_TITLE IN ({channels_str}) AND METRIC_DATE >= DATEADD(day, -{days_back}, CURRENT_DATE()) GROUP BY METRIC_DATE, CHANNEL_TITLE{vt_group}"
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
            exact_paths = [f"{local_path}/CHANNEL_TITLE={c}/*.parquet" for c in selected_channels]
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
        exact_paths = [f"s3://{bucket_name}/mart/{table_name.lower()}.parquet/CHANNEL_TITLE={c}/*.parquet" for c in selected_channels]
        target_path_sql = "[" + ", ".join([f"'{p}'" for p in exact_paths]) + "]"
            
    query = f"SELECT METRIC_DATE, CHANNEL_TITLE{vt_select}, SUM({metric_col}) as {metric_col} FROM read_parquet({target_path_sql}, hive_partitioning=1) WHERE CHANNEL_TITLE IN ({channels_str}) AND METRIC_DATE >= CURRENT_DATE() - INTERVAL {days_back} DAY GROUP BY METRIC_DATE, CHANNEL_TITLE{vt_group}"
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
            exact_paths = [f"{local_path}/CHANNEL_TITLE={c}/*.parquet" for c in selected_channels]
            target_path_sql = "[" + ", ".join([f"'{p}'" for p in exact_paths]) + "]"
        else:
            target_path_sql = f"'{local_path}'"
    else:
        bucket_name = _get_config("S3_BUCKET_NAME", "yt-sf-metrics-data-prod")
        import urllib.parse
        exact_paths = [f"s3://{bucket_name}/mart/{table_name.lower()}.parquet/CHANNEL_TITLE={c}/*.parquet" for c in selected_channels]
        target_path_sql = "[" + ", ".join([f"'{p}'" for p in exact_paths]) + "]"
            
    query = f"SELECT * FROM read_parquet({target_path_sql}, hive_partitioning=1) WHERE CHANNEL_TITLE IN ({channels_str}) AND METRIC_DATE = (SELECT MAX(METRIC_DATE) FROM read_parquet({target_path_sql}, hive_partitioning=1) WHERE CHANNEL_TITLE IN ({channels_str}))"
    df = con.execute(query).df()
    if 'METRIC_DATE' in df.columns: df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
    return df

@st.cache_data(ttl=3600, max_entries=2)
def get_top_n_channels_from_video(table_name: str = "RPT_VIDEO_PERFORMANCE_DAILY", n: int = 3) -> list:
    """
    Fetch the top N channels based on the sum of DAILY_VIEWS for the latest available date.
    Uses the pre-aggregated channel table for blazing fast global queries.
    """
    table_name = table_name.upper()
    
    # 1. Snowflake SiS
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        try:
            session.use_warehouse('YT_SF_REPORTING_WH')
        except Exception:
            pass
        query = f"""
            SELECT CHANNEL_TITLE
            FROM MART.RPT_CHANNEL_PERFORMANCE_DAILY
            WHERE METRIC_DATE = (SELECT MAX(METRIC_DATE) FROM MART.RPT_CHANNEL_PERFORMANCE_DAILY)
            ORDER BY DAILY_VIEWS DESC NULLS LAST
            LIMIT {n}
        """
        df = session.sql(query).to_pandas()
        return df['CHANNEL_TITLE'].tolist()
    except Exception:
        pass

    # For Local and S3, use DuckDB
    con = get_duckdb_connection()
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    local_path = os.path.join(project_root, "data", "export", "rpt_channel_performance_daily.parquet")
    
    if os.path.exists(local_path):
        target_path = local_path
    else:
        # Read from S3 via DuckDB httpfs
        bucket_name = _get_config("S3_BUCKET_NAME", "yt-sf-metrics-data-prod")
        aws_key = _get_config("AWS_ACCESS_KEY_ID")
        aws_secret = _get_config("AWS_SECRET_ACCESS_KEY")
        aws_region = _get_config("AWS_DEFAULT_REGION", "eu-north-1")
        target_path = f"s3://{bucket_name}/mart/rpt_channel_performance_daily.parquet"
        
        if aws_key and aws_secret:
            con.execute(f"SET s3_region='{aws_region}';")
            con.execute(f"SET s3_access_key_id='{aws_key}';")
            con.execute(f"SET s3_secret_access_key='{aws_secret}';")
            
    query = f"""
        SELECT CHANNEL_TITLE
        FROM read_parquet('{target_path}')
        WHERE METRIC_DATE = (SELECT MAX(METRIC_DATE) FROM read_parquet('{target_path}'))
        ORDER BY DAILY_VIEWS DESC NULLS LAST
        LIMIT {n}
    """
    try:
        con.execute("SET memory_limit='1GB';")
        df = con.execute(query).df()
        return df['CHANNEL_TITLE'].tolist()
    except Exception as e:
        # Fallback empty list
        return []

