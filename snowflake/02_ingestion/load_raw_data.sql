-- ============================================================
-- NorthStar Commerce
-- RAW ingestion from named internal stage
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE NORTHSTAR_WH;
USE DATABASE NORTHSTAR_DB;
USE SCHEMA RAW;

-- ============================================================
-- BATCH 1
-- ============================================================

COPY INTO RAW_CUSTOMERS
(
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    COUNTRY,
    SIGNUP_DATE,
    CUSTOMER_STATUS,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1::NUMBER,
        t.$2::VARCHAR,
        t.$3::VARCHAR,
        t.$4::VARCHAR,
        t.$5::VARCHAR,
        t.$6::DATE,
        t.$7::VARCHAR,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => CSV_FORMAT) t
)
PATTERN = '.*customers[.]csv.*'
ON_ERROR = ABORT_STATEMENT;

COPY INTO RAW_PRODUCTS
(
    PRODUCT_ID,
    PRODUCT_NAME,
    CATEGORY,
    UNIT_PRICE,
    IS_ACTIVE,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1::NUMBER,
        t.$2::VARCHAR,
        t.$3::VARCHAR,
        t.$4::NUMBER(10,2),
        t.$5::BOOLEAN,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => CSV_FORMAT) t
)
PATTERN = '.*products[.]csv.*'
ON_ERROR = ABORT_STATEMENT;

COPY INTO RAW_ORDERS
(
    ORDER_ID,
    CUSTOMER_ID,
    PRODUCT_ID,
    ORDER_DATE,
    QUANTITY,
    UNIT_PRICE,
    ORDER_STATUS,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1::NUMBER,
        t.$2::NUMBER,
        t.$3::NUMBER,
        t.$4::DATE,
        t.$5::NUMBER,
        t.$6::NUMBER(10,2),
        t.$7::VARCHAR,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => CSV_FORMAT) t
)
PATTERN = '.*orders[.]csv.*'
ON_ERROR = ABORT_STATEMENT;

COPY INTO RAW_WEB_EVENTS
(
    EVENT_DATA,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => JSON_FORMAT) t
)
PATTERN = '.*web_events[.]json.*'
ON_ERROR = ABORT_STATEMENT;

-- ============================================================
-- BATCH 2 (incremental load demo)
-- ============================================================

COPY INTO RAW_CUSTOMERS
(
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    COUNTRY,
    SIGNUP_DATE,
    CUSTOMER_STATUS,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1::NUMBER,
        t.$2::VARCHAR,
        t.$3::VARCHAR,
        t.$4::VARCHAR,
        t.$5::VARCHAR,
        t.$6::DATE,
        t.$7::VARCHAR,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => CSV_FORMAT) t
)
PATTERN = '.*customers_batch2[.]csv.*'
ON_ERROR = ABORT_STATEMENT;

COPY INTO RAW_PRODUCTS
(
    PRODUCT_ID,
    PRODUCT_NAME,
    CATEGORY,
    UNIT_PRICE,
    IS_ACTIVE,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1::NUMBER,
        t.$2::VARCHAR,
        t.$3::VARCHAR,
        t.$4::NUMBER(10,2),
        t.$5::BOOLEAN,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => CSV_FORMAT) t
)
PATTERN = '.*products_batch2[.]csv.*'
ON_ERROR = ABORT_STATEMENT;

COPY INTO RAW_ORDERS
(
    ORDER_ID,
    CUSTOMER_ID,
    PRODUCT_ID,
    ORDER_DATE,
    QUANTITY,
    UNIT_PRICE,
    ORDER_STATUS,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1::NUMBER,
        t.$2::NUMBER,
        t.$3::NUMBER,
        t.$4::DATE,
        t.$5::NUMBER,
        t.$6::NUMBER(10,2),
        t.$7::VARCHAR,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => CSV_FORMAT) t
)
PATTERN = '.*orders_batch2[.]csv.*'
ON_ERROR = ABORT_STATEMENT;

COPY INTO RAW_WEB_EVENTS
(
    EVENT_DATA,
    SOURCE_FILE,
    INGESTED_AT
)
FROM (
    SELECT
        t.$1,
        METADATA$FILENAME,
        METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
    FROM @NORTHSTAR_STAGE
        (FILE_FORMAT => JSON_FORMAT) t
)
PATTERN = '.*web_events_batch2[.]json.*'
ON_ERROR = ABORT_STATEMENT;

-- ============================================================
-- Validation
-- ============================================================

SELECT COUNT(*) AS CUSTOMER_ROWS FROM RAW_CUSTOMERS;
SELECT COUNT(*) AS PRODUCT_ROWS FROM RAW_PRODUCTS;
SELECT COUNT(*) AS ORDER_ROWS FROM RAW_ORDERS;
SELECT COUNT(*) AS EVENT_ROWS FROM RAW_WEB_EVENTS;
