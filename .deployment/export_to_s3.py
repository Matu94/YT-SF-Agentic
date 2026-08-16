#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def load_env():
    """Simple parser for .env file if it exists."""
    env_path = Path(".env")
    if env_path.is_file():
        print("Loading environment variables from .env...")
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = val.strip()

def main():
    load_env()
    
    # 1. Check Snowflake Configuration
    sf_required = ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_ROLE", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE")
    sf_missing = [v for v in sf_required if not os.environ.get(v)]
    if sf_missing:
        print(f"Error: Missing Snowflake environment variables: {', '.join(sf_missing)}")
        sys.exit(1)
        
    # 2. Check AWS Configuration
    aws_required = ("S3_BUCKET_NAME", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
    aws_missing = [v for v in aws_required if not os.environ.get(v)]
    if aws_missing:
        print(f"Error: Missing AWS environment variables: {', '.join(aws_missing)}")
        sys.exit(1)
        
    try:
        import snowflake.connector
    except ImportError:
        print("Error: snowflake-connector-python required. Run: pip install snowflake-connector-python[pandas]", file=sys.stderr)
        sys.exit(1)
        
    try:
        import pandas as pd
        import pyarrow  # implicitly required for pandas.to_parquet
        import s3fs     # implicitly required for pandas.to_parquet s3:// prefix
    except ImportError:
        print("Error: Pandas, PyArrow, and s3fs are required. Run: pip install pandas pyarrow s3fs", file=sys.stderr)
        sys.exit(1)

    # Establish Snowflake connection
    database = os.environ["SNOWFLAKE_DATABASE"].strip()
    params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"].strip(),
        "user": os.environ["SNOWFLAKE_USER"].strip(),
        "role": os.environ["SNOWFLAKE_ROLE"].strip(),
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"].strip(),
        "database": database,
        "schema": "MART"
    }
    
    # Handle authentication method (Key-Pair vs. SSO)
    key_path = os.path.expanduser("~/.snowflake/rsa_key.p8")
    if not os.path.isfile(key_path) and os.path.isfile(".snowflake/rsa_key.p8"):
        key_path = os.path.abspath(".snowflake/rsa_key.p8")
        
    if os.environ.get("SNOWFLAKE_PRIVATE_KEY"):
        # For CI/CD when raw private key is injected directly from secrets
        import base64
        import tempfile
        print("Using SNOWFLAKE_PRIVATE_KEY from environment...")
        
        # Write the key to a temporary file for the connector to read if it's base64 encoded
        # In our deployment workflow, we usually write it to .snowflake/rsa_key.p8
        # If it's available directly, use it. Here we rely on the .p8 file flow.
        pass
        
    if os.path.isfile(key_path):
        print(f"Using private key authentication: {key_path}")
        params["private_key_file"] = key_path
        passphrase = (os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASS") or os.environ.get("PRIVATE_KEY_PASSPHRASE") or "").strip()
        if passphrase:
            params["private_key_file_pwd"] = passphrase
        params["authenticator"] = "SNOWFLAKE_JWT"
    else:
        print("Using SSO (externalbrowser) authentication...")
        params["authenticator"] = "externalbrowser"
        
    bucket_name = os.environ["S3_BUCKET_NAME"].strip()
    aws_region = os.environ.get("AWS_DEFAULT_REGION", "eu-north-1").strip()
    
    VIEWS_TO_EXPORT = [
        "RPT_CHANNEL_PERFORMANCE_DAILY",
        "RPT_CHANNEL_PERFORMANCE_ROLLING_7D",
        "RPT_CHANNEL_PERFORMANCE_ROLLING_30D",
        "RPT_VIDEO_PERFORMANCE_DAILY",
        "RPT_VIDEO_PERFORMANCE_ROLLING_7D",
        "RPT_VIDEO_PERFORMANCE_ROLLING_30D",
        "RPT_TOP_VIDEO_BY_VIEWS",
        "RPT_TOP_VIDEO_BY_LIKES",
        "RPT_TOP_VIDEO_BY_COMMENTS"
    ]
    
    print(f"\n🚀 Connecting to Snowflake ({database}.MART)...")
    conn = snowflake.connector.connect(**params)
    try:
        cur = conn.cursor()
        
        print(f"📦 Exporting to AWS S3 Bucket: {bucket_name} ({aws_region})\n")
        
        storage_options = {
            "key": os.environ["AWS_ACCESS_KEY_ID"].strip(),
            "secret": os.environ["AWS_SECRET_ACCESS_KEY"].strip(),
            "client_kwargs": {"region_name": aws_region}
        }
        
        for view in VIEWS_TO_EXPORT:
            print(f"  -> Extracting {view}...")
            
            # Fetch data using Snowflake connector
            cur.execute(f"SELECT * FROM MART.{view}")
            df = cur.fetch_pandas_all()
            
            if df.empty:
                print(f"     ⚠️ Warning: View {view} is empty. Skipping export.")
                continue
                
            # Convert Snowflake column names (uppercase) to uppercase just to be safe
            df.columns = [col.upper() for col in df.columns]
            
            # Upload directly to S3 via Pandas and s3fs
            s3_path = f"s3://{bucket_name}/mart/{view.lower()}.parquet"
            print(f"     -> Uploading to {s3_path} ({len(df)} rows)")
            
            df.to_parquet(
                s3_path, 
                index=False,
                engine="pyarrow",
                storage_options=storage_options
            )
            print("     ✓ Done.")
            
        print("\n✅ All presentation views exported successfully!")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
