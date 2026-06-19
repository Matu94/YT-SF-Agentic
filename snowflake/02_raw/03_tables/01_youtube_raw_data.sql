-- 1. Create Persistent Raw Table for YouTube API Raw Data
-- Resides in RAW schema, meant for persistent historical storage of raw JSON.

CREATE OR REPLACE TABLE RAW.YOUTUBE_RAW_DATA (
    RAW_JSON VARIANT,
    EXTRACTED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
) CLUSTER BY (RAW_JSON:kind::string, EXTRACTED_AT::DATE);
