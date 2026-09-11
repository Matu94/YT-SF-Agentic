-- 1. Create View for Parsed Channels
-- Resides in RAW schema, flattens the raw channel JSON data from YOUTUBE_RAW_DATA.

CREATE OR REPLACE VIEW RAW.V_YOUTUBE_PARSED_CHANNELS AS
SELECT
    EXTRACTED_AT,
    value:id::STRING AS CHANNEL_ID,
    value:snippet.title::STRING AS CHANNEL_TITLE,
    value:snippet.customUrl::STRING AS CHANNEL_CUSTOM_URL,
    value:snippet.publishedAt::TIMESTAMP_TZ AS CHANNEL_PUBLISHED_AT,
    value:snippet.country::STRING AS CHANNEL_COUNTRY,
    value:statistics.subscriberCount::INTEGER AS TOTAL_SUBSCRIBERS,
    value:statistics.viewCount::INTEGER AS TOTAL_VIEWS,
    value:statistics.videoCount::INTEGER AS TOTAL_VIDEOS,
    value:contentDetails.relatedPlaylists.uploads::STRING AS UPLOADS_PLAYLIST_ID
FROM RAW.YOUTUBE_RAW_DATA,
LATERAL FLATTEN(INPUT => RAW_JSON:items)
WHERE RAW_JSON:kind::STRING = 'youtube#channelListResponse';
