CREATE STAGE IF NOT EXISTS MART.STREAMLIT_STAGE
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Stage for storing Snowflake Native Streamlit application files';
