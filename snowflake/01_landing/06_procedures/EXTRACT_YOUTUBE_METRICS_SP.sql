-- 1. Create Snowpark Python Stored Procedure for YouTube API Extraction
-- Resides in LANDING schema, executed by tasks or manually to load data to LANDING.
-- Depends on: 01_infrastructure and 02_integrations
-- Optimized per ADR-018: Chunked channel lookups, concurrent HTTP I/O, global video ID pooling, and single atomic bulk write.

CREATE OR REPLACE PROCEDURE LANDING.EXTRACT_YOUTUBE_METRICS_SP()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('snowflake-snowpark-python', 'requests')
EXTERNAL_ACCESS_INTEGRATIONS = ({{SNOWFLAKE_DATABASE}}_YOUTUBE_API_INTEGRATION)
SECRETS = ('youtube_api_key' = TECH.YOUTUBE_API_KEY_SECRET)
HANDLER = 'main'
EXECUTE AS CALLER
AS
$$
import _snowflake
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from snowflake.snowpark.functions import col, parse_json, sql_expr
import json
import logging

logger = logging.getLogger("extract_youtube_metrics")

MAX_BATCH_SIZE = 50
MAX_WORKERS = 8
REQUEST_TIMEOUT_SEC = 30


def build_http_session():
    """Creates a thread-safe requests.Session with connection pooling and exponential backoff retries."""
    http = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(
        pool_connections=MAX_WORKERS,
        pool_maxsize=MAX_WORKERS * 2,
        max_retries=retry_strategy
    )
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http


def fetch_playlist_video_ids(http, playlist_id, api_key):
    """Paginates through a channel's uploads playlist and returns all discovered video IDs."""
    video_ids = []
    next_page_token = None
    try:
        while True:
            params = {
                "part": "contentDetails",
                "playlistId": playlist_id,
                "maxResults": MAX_BATCH_SIZE,
                "key": api_key
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            pl_response = http.get(
                "https://youtube.googleapis.com/youtube/v3/playlistItems",
                params=params,
                timeout=REQUEST_TIMEOUT_SEC
            )
            pl_response.raise_for_status()
            pl_data = pl_response.json()

            for item in pl_data.get("items", []):
                video_id = item.get("contentDetails", {}).get("videoId")
                if video_id:
                    video_ids.append(video_id)

            next_page_token = pl_data.get("nextPageToken")
            if not next_page_token:
                break
    except requests.exceptions.HTTPError as http_err:
        # Per-channel fault isolation: log empty/missing uploads playlists without aborting the entire batch
        logger.warning(f"Skipping playlist {playlist_id} due to HTTP error: {str(http_err)}")
    return video_ids


def fetch_video_batch_payload(http, batch_ids, api_key):
    """Fetches video statistics for a batch of up to 50 video IDs and returns the serialized JSON payload."""
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": ",".join(batch_ids),
        "key": api_key
    }
    v_response = http.get(
        "https://youtube.googleapis.com/youtube/v3/videos",
        params=params,
        timeout=REQUEST_TIMEOUT_SEC
    )
    v_response.raise_for_status()
    return json.dumps(v_response.json())


def main(session):
    try:
        # Set session timezone to Budapest to ensure EXTRACTED_AT defaults correctly (ADR-005)
        session.sql("ALTER SESSION SET TIMEZONE = 'Europe/Budapest'").collect()

        # Truncate the transient landing table before each new extraction run
        session.sql("TRUNCATE TABLE {{SNOWFLAKE_DATABASE}}.LANDING.YOUTUBE_RAW_DATA").collect()

        # Retrieve the API key securely
        api_key = _snowflake.get_generic_secret_string('youtube_api_key')

        # Target Channels
        channel_ids = [
            'UCIITmFAHQ4S1FMDWqhZyQKg', 
            'UC9qpYwK7N9EB0-SECANa23g', 
            'UCDwyp7fW0R8b27muWFEAgvQ', 
            'UC3T5ogRHZVB3jEO5WFvzmIQ', 
            'UCpj5XSIwGUaaoVDZnVCBj8Q', 
            'UCfS72Yr7hFsHClD3krlP9UA', 
            'UCcSAt9uIqRHK8dEV2wVY1dQ', 
            'UC1R3yteq3HoSUIHQ7hp65XQ',
            'UCHnd8KvQyMGU0DAlJSuYwhw', 
            'UCgP9ETA61mi7UwMbbkVsCSQ', 
            'UC3BxSWxHi_Xt7Bt8wyzzg_A', 
            'UC4IW7JBJtOJ8zkIpzg31NwQ', 
            'UCelRSBU3d8DGR04CNNubTdQ', 
            'UCoXnnnrdhaKljuhA2IrIhVQ', 
            'UCVIyRUt03aABOiSAWLegy2w', 
            'UCWALLPCVkSyKLuZLg5bc3QQ', 
            'UCjn8OWDk9_COueCW6oE2j7Q', 
            'UCrpWCVp9FuGA8OnGtA0rgsw', 
            'UCSFMCn1xtj_4kOy6KNK_fNg', 
            'UCTY9vSAwOVsXw1lE1vBD0Hg', 
            'UCnoVsxmXRCq3935G40SdBKA', 
            'UCDeRsDqcB8zdkzErxrdHCOw', 
            'UCQYlMOshLHIfOqjZjlpkLyQ', 
            'UCM-1sd-cXSuCsfWp8QMY_OQ', 
            'UCGoLa-QhHmTxLEdjv_8dxrg', 
            'UCw0oJgCjz3NvAICbqWImH-A', 
            'UCEFpEvuosfPGlV1VyUF6QOA', 
            'UCXxUjsYxbL1llIe9Ra6wcyQ', 
            'UCFLj8uVcUemF9nF3rQzc-CA', 
            'UCtWF535qAafjOpd2ggmdpzg', 
            'UCuFWG5idQ00n4mrYNFZYhOQ', 
            'UCsiq8vuWW1NdGkaspTLfr0g', 
            'UCt2uo4f6EtHnBjicvUkOz_w', 
            'UCVoGCDIv8h3OkzZYySWK6lw', 
            'UCoZMTeYtBas2Fn2pbIsq-Pw', 
            'UCkXZcdClprjcI4gWeFuB7Qw',
            'UC8BRuUwMn6_ObKHR0XwqgcA',
            'UCh6iuFfjjNrZMZVaqdwxCzA',
            'UCDHjSN4vbfmzb8Cdfsob9Gg',
            'UCnvLehvGPkEo51cDfJ_Chzw',
            'UCHd7a3FbnCbCGrmQ4uNPXdQ',
            'UCZ_VmmxmXN8Bjyfuo2vUe6Q',
            'UC_fAjvoGnqySaNM6DRfFiCA',
            'UCZGa9_7P0naz0iMUe2VoX0w'
        ]

        raw_payloads = []
        uploads_playlist_ids = []
        http = build_http_session()

        # 1. Fetch channel details in chunks of up to 50 channel IDs (ADR-018)
        for i in range(0, len(channel_ids), MAX_BATCH_SIZE):
            channel_chunk = channel_ids[i:i + MAX_BATCH_SIZE]
            c_response = http.get(
                "https://youtube.googleapis.com/youtube/v3/channels",
                params={
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(channel_chunk),
                    "key": api_key
                },
                timeout=REQUEST_TIMEOUT_SEC
            )
            c_response.raise_for_status()
            c_data = c_response.json()
            raw_payloads.append((json.dumps(c_data),))

            for item in c_data.get("items", []):
                uploads_id = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                if uploads_id:
                    uploads_playlist_ids.append(uploads_id)

        # 2. Harvest all video IDs concurrently across all channels' uploads playlists
        all_video_ids = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            playlist_futures = [
                executor.submit(fetch_playlist_video_ids, http, pl_id, api_key)
                for pl_id in uploads_playlist_ids
            ]
            for future in as_completed(playlist_futures):
                all_video_ids.extend(future.result())

        # 3. Pool and deduplicate video IDs globally before slicing into exact 50-ID batches
        unique_video_ids = list(dict.fromkeys(all_video_ids))
        video_batches = [
            unique_video_ids[i:i + MAX_BATCH_SIZE]
            for i in range(0, len(unique_video_ids), MAX_BATCH_SIZE)
        ]

        # 4. Fetch video statistics concurrently in batches of 50
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            video_futures = [
                executor.submit(fetch_video_batch_payload, http, batch, api_key)
                for batch in video_batches
            ]
            for future in as_completed(video_futures):
                raw_payloads.append((future.result(),))

        # 5. Single atomic bulk write into LANDING.YOUTUBE_RAW_DATA
        if raw_payloads:
            df = session.create_dataframe(raw_payloads, schema=["RAW_JSON_STR"])
            df_to_write = df.select(
                parse_json(col("RAW_JSON_STR")).alias("RAW_JSON"),
                sql_expr("CURRENT_TIMESTAMP()::TIMESTAMP_NTZ").alias("EXTRACTED_AT")
            )
            df_to_write.write.save_as_table(
                "{{SNOWFLAKE_DATABASE}}.LANDING.YOUTUBE_RAW_DATA",
                mode="append"
            )

        return (
            f"SUCCESS: Extracted {len(channel_ids)} channels and {len(unique_video_ids)} videos "
            f"in {len(raw_payloads)} batched JSON payloads."
        )
    except Exception as e:
        logger.error(f"Error extracting YouTube metrics: {str(e)}")
        return f"FAILED: {str(e)}"
$$;
