-- ============================================================
-- NorthStar Commerce
-- Metadata-Driven Data Quality Framework
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE NORTHSTAR_WH;
USE DATABASE NORTHSTAR_DB;
USE SCHEMA CONTROL;


CREATE OR REPLACE TABLE DQ_RULES
(
    RULE_ID             NUMBER,
    DOMAIN              VARCHAR,
    TARGET_TABLE        VARCHAR,
    CHECK_NAME          VARCHAR,
    FAILURE_CONDITION   VARCHAR,
    SEVERITY            VARCHAR,
    ENABLED             BOOLEAN,
    COMMENT             VARCHAR
);


INSERT INTO DQ_RULES
VALUES
    (1, 'ORDERS', 'NORTHSTAR_DB.SILVER.ORDERS',
     'INVALID_ORDER',
     'IS_VALID_ORDER = FALSE',
     'HIGH', TRUE,
     'Order fails one or more validation rules'),

    (2, 'ORDERS', 'NORTHSTAR_DB.SILVER.ORDERS',
     'INVALID_CUSTOMER',
     'IS_CUSTOMER_VALID = FALSE',
     'HIGH', TRUE,
     'Order references an unknown customer'),

    (3, 'ORDERS', 'NORTHSTAR_DB.SILVER.ORDERS',
     'INVALID_QUANTITY',
     'IS_QUANTITY_VALID = FALSE',
     'HIGH', TRUE,
     'Order quantity must be greater than zero'),

    (4, 'ORDERS', 'NORTHSTAR_DB.SILVER.ORDERS',
     'INVALID_PRICE',
     'IS_PRICE_VALID = FALSE',
     'HIGH', TRUE,
     'Unit price cannot be negative'),

    (5, 'ORDERS', 'NORTHSTAR_DB.SILVER.ORDERS',
     'MISSING_ORDER_ID',
     'ORDER_ID IS NULL',
     'CRITICAL', TRUE,
     'Order identifier cannot be null'),

    (6, 'CUSTOMERS', 'NORTHSTAR_DB.SILVER.CUSTOMERS',
     'MISSING_EMAIL',
     'EMAIL IS NULL',
     'MEDIUM', TRUE,
     'Customer email is missing'),

    (7, 'WEB_EVENTS', 'NORTHSTAR_DB.SILVER.WEB_EVENTS',
     'INVALID_CUSTOMER',
     'IS_CUSTOMER_VALID = FALSE',
     'HIGH', TRUE,
     'Event references an unknown customer'),

    (8, 'WEB_EVENTS', 'NORTHSTAR_DB.SILVER.WEB_EVENTS',
     'INCOMPLETE_EVENT',
     'IS_EVENT_COMPLETE = FALSE',
     'HIGH', TRUE,
     'Required event attributes are missing'),

    (9, 'CUSTOMERS', 'NORTHSTAR_DB.SILVER.CUSTOMERS',
     'INVALID_CUSTOMER_STATUS',
     'CUSTOMER_STATUS NOT IN (''ACTIVE'', ''INACTIVE'')',
     'MEDIUM', TRUE,
     'Customer status must belong to the accepted domain');


CREATE TABLE IF NOT EXISTS DQ_RUN_RESULTS
(
    RUN_ID          VARCHAR,
    RULE_ID         NUMBER,
    DOMAIN          VARCHAR,
    TARGET_TABLE    VARCHAR,
    CHECK_NAME      VARCHAR,
    SEVERITY        VARCHAR,
    FAILED_ROWS     NUMBER,
    STATUS          VARCHAR,
    CHECKED_AT      TIMESTAMP_LTZ
);