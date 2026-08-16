import os
import pandas as pd
import streamlit as st

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
        return session.sql(f"SELECT * FROM MART.{table_name}").to_pandas()
    except Exception:
        pass  # Not executing inside a Snowflake-hosted Streamlit container

    # 2. Attempt local Parquet fallback (useful for local dev/testing without network)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    local_path = os.path.join(project_root, "data", "export", f"{table_name.lower()}.parquet")
    if os.path.exists(local_path):
        return pd.read_parquet(local_path)

    def _get_config(key: str, default: str | None = None) -> str | None:
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
        return os.getenv(key, default)

    # 3. Read from S3 bucket (Streamlit Community Cloud)
    bucket_name = _get_config("S3_BUCKET_NAME", "yt-sf-metrics-data-prod")
    s3_path = f"s3://{bucket_name}/mart/{table_name.lower()}.parquet"

    storage_options = {}
    aws_key = _get_config("AWS_ACCESS_KEY_ID")
    aws_secret = _get_config("AWS_SECRET_ACCESS_KEY")
    aws_region = _get_config("AWS_DEFAULT_REGION", "eu-north-1")

    if aws_key and aws_secret:
        storage_options = {
            "key": aws_key,
            "secret": aws_secret,
            "client_kwargs": {"region_name": aws_region}
        }

    return pd.read_parquet(s3_path, storage_options=storage_options if storage_options else None)


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
