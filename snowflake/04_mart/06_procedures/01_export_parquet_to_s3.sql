-- ==============================================================
-- 01_export_parquet_to_s3.sql
-- Procedure to export all RPT_* views to S3 Parquet
-- ==============================================================

CREATE OR REPLACE PROCEDURE MART.EXPORT_MART_TO_S3()
  RETURNS VARCHAR
  LANGUAGE SQL
  EXECUTE AS CALLER
AS
$$
DECLARE
  view_name VARCHAR;
  select_list VARCHAR;
  export_sql VARCHAR;
  result_msg VARCHAR DEFAULT 'Export completed for: ';
  c1 CURSOR FOR 
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.VIEWS 
    WHERE TABLE_SCHEMA = 'MART' 
      AND TABLE_NAME LIKE 'RPT_%'
    ORDER BY TABLE_NAME;
BEGIN
  FOR record IN c1 DO
    view_name := record.TABLE_NAME;
    
    -- Dynamically build column list casting TIMESTAMP_TZ/LTZ to TIMESTAMP_NTZ (required by Parquet format)
    SELECT LISTAGG(
      CASE 
        WHEN DATA_TYPE IN ('TIMESTAMP_TZ', 'TIMESTAMP_LTZ') 
          THEN 'CONVERT_TIMEZONE(\'UTC\', "' || COLUMN_NAME || '")::TIMESTAMP_NTZ AS "' || COLUMN_NAME || '"'
        ELSE '"' || COLUMN_NAME || '"'
      END, 
      ', '
    ) WITHIN GROUP (ORDER BY ORDINAL_POSITION)
    INTO :select_list
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'MART' 
      AND TABLE_NAME = :view_name;
    
    IF (view_name LIKE 'RPT_VIDEO_PERFORMANCE%') THEN
      export_sql := 'COPY INTO @MART.S3_EXPORT_STAGE/' || LOWER(view_name) || '.parquet/ ' ||
                    'FROM (SELECT ' || select_list || ' FROM MART."' || view_name || '") ' ||
                    'PARTITION BY (''CHANNEL_TITLE='' || CHANNEL_TITLE) ' ||
                    'FILE_FORMAT = (TYPE = PARQUET COMPRESSION = SNAPPY) ' ||
                    'HEADER = TRUE ' ||
                    'OVERWRITE = TRUE ' ||
                    'MAX_FILE_SIZE = 5368709120;';
    ELSE
      export_sql := 'COPY INTO @MART.S3_EXPORT_STAGE/' || LOWER(view_name) || '.parquet ' ||
                    'FROM (SELECT ' || select_list || ' FROM MART."' || view_name || '") ' ||
                    'FILE_FORMAT = (TYPE = PARQUET COMPRESSION = SNAPPY) ' ||
                    'HEADER = TRUE ' ||
                    'OVERWRITE = TRUE ' ||
                    'SINGLE = TRUE ' ||
                    'MAX_FILE_SIZE = 5368709120;';
    END IF;
    
    EXECUTE IMMEDIATE :export_sql;
    result_msg := result_msg || view_name || ', ';
  END FOR;
  
  RETURN result_msg;
END;
$$;
