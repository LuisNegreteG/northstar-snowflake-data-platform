-- ============================================================
-- NorthStar Commerce
-- Native dbt Production Orchestration
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE NORTHSTAR_WH;
USE DATABASE NORTHSTAR_DB;
USE SCHEMA CONTROL;


-- ============================================================
-- SCHEDULED PRODUCTION DBT BUILD
-- ============================================================

CREATE OR ALTER TASK
    NORTHSTAR_DB.CONTROL.NORTHSTAR_DBT_PROD_TASK

    WAREHOUSE = NORTHSTAR_WH

    SCHEDULE = '6 HOURS'

AS

    EXECUTE DBT PROJECT
        NORTHSTAR_DB.CONTROL.NORTHSTAR_DBT_PROJECT
        ARGS = 'build --target prod';


-- Keep disabled by default to avoid unnecessary compute usage
-- when cloning or reviewing this portfolio project.

ALTER TASK
    NORTHSTAR_DB.CONTROL.NORTHSTAR_DBT_PROD_TASK
SUSPEND;


-- To activate:
--
-- ALTER TASK
-- NORTHSTAR_DB.CONTROL.NORTHSTAR_DBT_PROD_TASK
-- RESUME;