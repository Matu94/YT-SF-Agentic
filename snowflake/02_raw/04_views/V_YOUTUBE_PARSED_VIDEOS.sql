-- 2. Create View for Parsed Videos
-- Resides in RAW schema, flattens the raw video list JSON data from YOUTUBE_RAW_DATA.

CREATE OR REPLACE VIEW RAW.V_YOUTUBE_PARSED_VIDEOS AS
SELECT
    EXTRACTED_AT,
    value:id::STRING AS VIDEO_ID,
    value:snippet.channelId::STRING AS CHANNEL_ID,
    value:snippet.title::STRING AS VIDEO_TITLE,
    value:snippet.publishedAt::TIMESTAMP_TZ AS PUBLISHED_AT,
    value:contentDetails.duration::STRING AS DURATION_ISO8601,
    value:snippet.liveBroadcastContent::STRING AS LIVE_BROADCAST_CONTENT,
    value:statistics.viewCount::INTEGER AS TOTAL_VIEWS,
    value:statistics.likeCount::INTEGER AS TOTAL_LIKES,
    value:statistics.commentCount::INTEGER AS TOTAL_COMMENTS
FROM RAW.YOUTUBE_RAW_DATA,
LATERAL FLATTEN(INPUT => RAW_JSON:items)
WHERE RAW_JSON:kind::STRING = 'youtube#videoListResponse';
