-- 1. Create Snowpark Python Stored Procedure for YouTube API Extraction
-- Resides in TECH schema, executed by tasks or manually to load data to LANDING.
-- Depends on: 01_infrastructure and 02_integrations

CREATE OR REPLACE PROCEDURE TECH.EXTRACT_YOUTUBE_METRICS()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('snowflake-snowpark-python', 'requests')
EXTERNAL_ACCESS_INTEGRATIONS = (YT_SF_{{SNOWFLAKE_ENVIRONMENT}}_YOUTUBE_API_INTEGRATION)
SECRETS = ('youtube_api_key' = TECH.YOUTUBE_API_KEY_SECRET)
HANDLER = 'main'
EXECUTE AS CALLER
AS
$$
import _snowflake
import requests
import json
import logging

logger = logging.getLogger("extract_youtube_metrics")

def main(session):
    try:
        # Retrieve the API key securely
        api_key = _snowflake.get_generic_secret_string('youtube_api_key')
        
        # Phase 1 Target Channels
        # These are placeholders and should ideally be read from a config table in the future
        channel_ids = [
            'UC', # Replace with Fókusz Csoport ID
            'UC', # Replace with Jólvanezígy ID
            'UC', # Replace with Kókusz Plusz ID
            'UC'  # Replace with Világjegy Csatorna ID
        ]
        
        # Example API Call Structure (to be fully implemented once LANDING tables exist)
        # for channel_id in channel_ids:
        #     url = f"https://youtube.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={api_key}"
        #     response = requests.get(url)
        #     response.raise_for_status()
        #     data = response.json()
        #     
        #     # The data would then be inserted into a variant column in the LANDING layer
        #     # session.sql(f"INSERT INTO YT_SF_{{SNOWFLAKE_ENVIRONMENT}}.LANDING.RAW_YOUTUBE_CHANNELS (raw_data) SELECT PARSE_JSON('{json.dumps(data)}')").collect()
        
        return "SUCCESS: YouTube extraction procedure initialized successfully."
    except Exception as e:
        logger.error(f"Error extracting YouTube metrics: {str(e)}")
        return f"FAILED: {str(e)}"
$$;

-- Grant execution to LOAD role
GRANT USAGE ON PROCEDURE TECH.EXTRACT_YOUTUBE_METRICS() TO ROLE YT_SF_{{SNOWFLAKE_ENVIRONMENT}}_LOAD_ROLE;
