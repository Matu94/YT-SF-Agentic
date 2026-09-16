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
  c1 CURSOR FOR 
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.VIEWS 
    WHERE TABLE_SCHEMA = 'MART' 
      AND TABLE_NAME LIKE 'RPT_%';
  export_sql VARCHAR;
  result_msg VARCHAR DEFAULT 'Export completed for: ';
BEGIN
  FOR record IN c1 DO
    view_name := record.TABLE_NAME;
    export_sql := 'COPY INTO @S3_EXPORT_STAGE/' || LOWER(view_name) || '.parquet ' ||
                  'FROM ' || view_name || ' ' ||
                  'FILE_FORMAT = (TYPE = PARQUET) ' ||
                  'HEADER = TRUE ' ||
                  'OVERWRITE = TRUE ' ||
                  'SINGLE = TRUE;';
    
    EXECUTE IMMEDIATE :export_sql;
    result_msg := result_msg || view_name || ', ';
  END FOR;
  
  RETURN result_msg;
END;
$$;
