-- ============================================================
-- NorthStar Commerce
-- Explicit CDC Pipeline
-- Stream -> Triggered Task -> MERGE
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE NORTHSTAR_WH;
USE DATABASE NORTHSTAR_DB;


-- ============================================================
-- CDC SOURCE
-- Simulates an operational customer table
-- ============================================================

CREATE OR REPLACE TABLE NORTHSTAR_DB.RAW.CUSTOMER_CDC_SOURCE AS
SELECT
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    COUNTRY,
    CUSTOMER_STATUS,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS UPDATED_AT

FROM NORTHSTAR_DB.SILVER.CUSTOMERS;


-- ============================================================
-- CURRENT-STATE TARGET
-- ============================================================

CREATE OR REPLACE TABLE NORTHSTAR_DB.SILVER.CUSTOMER_CURRENT AS
SELECT
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    COUNTRY,
    CUSTOMER_STATUS,
    UPDATED_AT,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ AS DWH_UPDATED_AT

FROM NORTHSTAR_DB.RAW.CUSTOMER_CDC_SOURCE;


-- ============================================================
-- CHANGE DATA CAPTURE STREAM
-- ============================================================

CREATE OR REPLACE STREAM
    NORTHSTAR_DB.RAW.CUSTOMER_CDC_STREAM
ON TABLE
    NORTHSTAR_DB.RAW.CUSTOMER_CDC_SOURCE;


-- ============================================================
-- EVENT-DRIVEN CDC TASK
-- ============================================================

CREATE OR REPLACE TASK
    NORTHSTAR_DB.CONTROL.CUSTOMER_CDC_TASK

    WAREHOUSE = NORTHSTAR_WH

    WHEN SYSTEM$STREAM_HAS_DATA(
        'NORTHSTAR_DB.RAW.CUSTOMER_CDC_STREAM'
    )

AS

MERGE INTO NORTHSTAR_DB.SILVER.CUSTOMER_CURRENT AS tgt

USING (

    SELECT
        CUSTOMER_ID,
        FIRST_NAME,
        LAST_NAME,
        EMAIL,
        COUNTRY,
        CUSTOMER_STATUS,
        UPDATED_AT,
        METADATA$ACTION AS CDC_ACTION,
        METADATA$ISUPDATE AS CDC_IS_UPDATE

    FROM NORTHSTAR_DB.RAW.CUSTOMER_CDC_STREAM

) src

ON tgt.CUSTOMER_ID = src.CUSTOMER_ID


-- True DELETE
WHEN MATCHED
    AND src.CDC_ACTION = 'DELETE'
    AND src.CDC_IS_UPDATE = FALSE
THEN DELETE


-- New image of an UPDATE
WHEN MATCHED
    AND src.CDC_ACTION = 'INSERT'
THEN UPDATE SET

    tgt.FIRST_NAME = src.FIRST_NAME,
    tgt.LAST_NAME = src.LAST_NAME,
    tgt.EMAIL = src.EMAIL,
    tgt.COUNTRY = src.COUNTRY,
    tgt.CUSTOMER_STATUS = src.CUSTOMER_STATUS,
    tgt.UPDATED_AT = src.UPDATED_AT,
    tgt.DWH_UPDATED_AT = CURRENT_TIMESTAMP()


-- Brand-new INSERT
WHEN NOT MATCHED
    AND src.CDC_ACTION = 'INSERT'
THEN INSERT
(
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    COUNTRY,
    CUSTOMER_STATUS,
    UPDATED_AT,
    DWH_UPDATED_AT
)
VALUES
(
    src.CUSTOMER_ID,
    src.FIRST_NAME,
    src.LAST_NAME,
    src.EMAIL,
    src.COUNTRY,
    src.CUSTOMER_STATUS,
    src.UPDATED_AT,
    CURRENT_TIMESTAMP()
);


-- Task intentionally remains suspended in the portfolio setup.
-- Enable when CDC processing is required:
--
-- ALTER TASK NORTHSTAR_DB.CONTROL.CUSTOMER_CDC_TASK RESUME;