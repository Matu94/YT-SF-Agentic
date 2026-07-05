-- 1. Create Snowpark Python Stored Procedure for YouTube API Extraction
-- Resides in LANDING schema, executed by tasks or manually to load data to LANDING.
-- Depends on: 01_infrastructure and 02_integrations

CREATE OR REPLACE PROCEDURE LANDING.EXTRACT_YOUTUBE_METRICS_SP()
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
        # Set session timezone to Budapest to ensure EXTRACTED_AT defaults correctly
        session.sql("ALTER SESSION SET TIMEZONE = 'Europe/Budapest'").collect()

        # Truncate the transient landing table before each new extraction run
        session.sql("TRUNCATE TABLE YT_SF_{{SNOWFLAKE_ENVIRONMENT}}.LANDING.YOUTUBE_RAW_DATA").collect()

        # Retrieve the API key securely
        api_key = _snowflake.get_generic_secret_string('youtube_api_key')
        
        # Phase 1 Target Channels
        # These are placeholders and should ideally be read from a config table in the future
        channel_ids = [
            'UCIITmFAHQ4S1FMDWqhZyQKg', # Fókusz Csoport
            'UC9qpYwK7N9EB0-SECANa23g', # Jólvanezígy
            'UCDwyp7fW0R8b27muWFEAgvQ', # Világjegy
            'UCSFMCn1xtj_4kOy6KNK_fNg', # TheVR Gaming+
            'UCTY9vSAwOVsXw1lE1vBD0Hg', # theVR Podcast
            'UCQYlMOshLHIfOqjZjlpkLyQ'  # Aputest Podcast

        ]
        
        # Call YouTube API and Insert into LANDING table
        for channel_id in channel_ids:
            # 1. Fetch channel details
            url = f"https://youtube.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={channel_id}&key={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Serialize and insert channel data
            json_str = json.dumps(data).replace("\\", "\\\\").replace("'", "''")
            query = f"INSERT INTO YT_SF_{{SNOWFLAKE_ENVIRONMENT}}.LANDING.YOUTUBE_RAW_DATA (RAW_JSON) SELECT PARSE_JSON('{json_str}')"
            session.sql(query).collect()
            
            # 2. Extract 'uploads' playlist ID
            items = data.get('items', [])
            if not items:
                continue
            uploads_playlist_id = items[0].get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            if not uploads_playlist_id:
                continue
            
            # 3. Harvest all video IDs via playlistItems pagination
            video_ids = []
            next_page_token = None
            while True:
                playlist_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={uploads_playlist_id}&maxResults=50&key={api_key}"
                if next_page_token:
                    playlist_url += f"&pageToken={next_page_token}"
                
                pl_response = requests.get(playlist_url)
                pl_response.raise_for_status()
                pl_data = pl_response.json()
                
                for item in pl_data.get('items', []):
                    video_id = item.get('contentDetails', {}).get('videoId')
                    if video_id:
                        video_ids.append(video_id)
                
                next_page_token = pl_data.get('nextPageToken')
                if not next_page_token:
                    break
            
            # 4. Fetch video statistics in batches of 50
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                ids_str = ",".join(batch_ids)
                
                videos_url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={ids_str}&key={api_key}"
                v_response = requests.get(videos_url)
                v_response.raise_for_status()
                v_data = v_response.json()
                
                # Serialize and insert video data
                v_json_str = json.dumps(v_data).replace("\\", "\\\\").replace("'", "''")
                v_query = f"INSERT INTO YT_SF_{{SNOWFLAKE_ENVIRONMENT}}.LANDING.YOUTUBE_RAW_DATA (RAW_JSON) SELECT PARSE_JSON('{v_json_str}')"
                session.sql(v_query).collect()
        
        return "SUCCESS: YouTube extraction procedure initialized successfully."
    except Exception as e:
        logger.error(f"Error extracting YouTube metrics: {str(e)}")
        return f"FAILED: {str(e)}"
$$;
