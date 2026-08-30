import os
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

@st.cache_data(ttl=3600)
def load_data(table_name: str) -> pd.DataFrame:
    """
    Unified Data Loader for Streamlit.
    Detects if running inside Snowflake (SiS) or Streamlit Community Cloud (S3/Parquet).
    
    Order of Evaluation:
    1. Active Snowflake Session (Streamlit in Snowflake - SiS)
    2. Local Parquet export file (for offline local development)
    3. AWS S3 Parquet file (Streamlit Community Cloud static mode)
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


    # 3. Read from S3 bucket (Streamlit Community Cloud)
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

@st.cache_data(ttl=3600)
def load_filtered_video_data(table_name: str, selected_channels: list, days_back: int = 40) -> pd.DataFrame:
    """
    Loads large video tables using Pushdown Predicates (DuckDB / SQL) 
    so only the selected channels are fetched into Memory.
    """
    if not selected_channels:
        return pd.DataFrame()
        
    table_name = table_name.upper()
    
    # 1. Snowflake SiS
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        try:
            session.use_warehouse('YT_SF_REPORTING_WH')
        except Exception:
            pass
        channels_sql = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in selected_channels])
        query = f"SELECT * FROM MART.{table_name} WHERE CHANNEL_TITLE IN ({channels_sql}) AND METRIC_DATE >= DATEADD(day, -{days_back}, CURRENT_DATE())"
        df = session.sql(query).to_pandas()
        if 'METRIC_DATE' in df.columns: 
            df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
        return df
    except Exception:
        pass

    # For Local and S3, use DuckDB
    import duckdb
    con = duckdb.connect(database=':memory:')
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    local_path = os.path.join(project_root, "data", "export", f"{table_name.lower()}.parquet")
    
    if os.path.exists(local_path):
        target_path = local_path
    else:
        # 3. Read from S3 via DuckDB httpfs
        con.execute("INSTALL httpfs; LOAD httpfs;")
        bucket_name = _get_config("S3_BUCKET_NAME", "yt-sf-metrics-data-prod")
        aws_key = _get_config("AWS_ACCESS_KEY_ID")
        aws_secret = _get_config("AWS_SECRET_ACCESS_KEY")
        aws_region = _get_config("AWS_DEFAULT_REGION", "eu-north-1")
        target_path = f"s3://{bucket_name}/mart/{table_name.lower()}.parquet"
        
        if aws_key and aws_secret:
            con.execute(f"SET s3_region='{aws_region}';")
            con.execute(f"SET s3_access_key_id='{aws_key}';")
            con.execute(f"SET s3_secret_access_key='{aws_secret}';")
            
    # Escape quotes in channel names for SQL
    channels_str = ", ".join([f"'{c.replace(chr(39), chr(39)+chr(39))}'" for c in selected_channels])
    
    query = f"""
        SELECT * 
        FROM read_parquet('{target_path}')
        WHERE CHANNEL_TITLE IN ({channels_str})
          AND METRIC_DATE >= CURRENT_DATE() - INTERVAL {days_back} DAY
    """
    try:
        df = con.execute(query).df()
        if 'METRIC_DATE' in df.columns:
            df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])
        return df
    except Exception as e:
        raise RuntimeError(f"DuckDB failed to fetch '{target_path}'. Details: {e}") from e
