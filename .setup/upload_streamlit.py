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
                os.environ[key.strip()] = val.strip()

def main():
    load_env()
    
    # Check required variables
    required = ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_ROLE", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE")
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("Please configure .env first.")
        sys.exit(1)
        
    try:
        import snowflake.connector
    except ImportError:
        print("Error: snowflake-connector-python required. Run: pip install snowflake-connector-python", file=sys.stderr)
        sys.exit(1)

    # Establish Snowflake connection
    database = os.environ["SNOWFLAKE_DATABASE"].strip()
    params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"].strip(),
        "user": os.environ["SNOWFLAKE_USER"].strip(),
        "role": os.environ["SNOWFLAKE_ROLE"].strip(),
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"].strip(),
        "database": database,
    }
    
    # Handle authentication method (Key-Pair vs. SSO)
    key_path = os.path.expanduser("~/.snowflake/rsa_key.p8")
    if not os.path.isfile(key_path) and os.path.isfile(".snowflake/rsa_key.p8"):
        key_path = os.path.abspath(".snowflake/rsa_key.p8")
        
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
        
    conn = snowflake.connector.connect(**params)
    try:
        cur = conn.cursor()
        
        # Verify schema and stage existence
        stage_schema = "MART"
        stage_name = "STREAMLIT_STAGE"
        full_stage = f"{database}.{stage_schema}.{stage_name}"
        
        # Check if the stage exists
        cur.execute(
            "SELECT 1 FROM INFORMATION_SCHEMA.STAGES "
            "WHERE STAGE_CATALOG = %s AND STAGE_SCHEMA = %s AND STAGE_NAME = %s",
            (database.upper(), stage_schema, stage_name),
        )
        if not cur.fetchone():
            print(f"Error: Stage '{full_stage}' does not exist. Please run DDL deployment first.")
            sys.exit(1)
            
        # Files to upload and their relative folders in the stage
        files_to_upload = {
            "streamlit/Home.py": "",
            "streamlit/environment.yml": "",
            "streamlit/pages/1_Channel_Info.py": "pages",
        }
        
        print(f"Uploading files to stage @{full_stage}...")
        for local_path, stage_subdir in files_to_upload.items():
            if not os.path.exists(local_path):
                print(f"  ⚠️ Warning: Local file '{local_path}' not found, skipping.", file=sys.stderr)
                continue
            
            stage_target = f"@{full_stage}"
            if stage_subdir:
                stage_target = f"{stage_target}/{stage_subdir}"
                
            abs_path = os.path.abspath(local_path)
            put_sql = f"PUT file://{abs_path} {stage_target} AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
            print(f"  Uploading: {local_path} -> {stage_target}")
            cur.execute(put_sql)
            # Drain result sets
            while True:
                try:
                    cur.fetchall()
                except Exception:
                    pass
                if not cur.nextset():
                    break
        print("✓ Streamlit files uploaded successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
