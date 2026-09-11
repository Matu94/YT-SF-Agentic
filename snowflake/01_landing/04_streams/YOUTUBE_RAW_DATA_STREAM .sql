-- 1. Create Stream on Landing Table
-- Resides in LANDING schema, captures new raw JSON drops for downstream loading.

CREATE OR REPLACE STREAM LANDING.YOUTUBE_RAW_DATA_STREAM 
ON TABLE LANDING.YOUTUBE_RAW_DATA 
APPEND_ONLY = TRUE;
