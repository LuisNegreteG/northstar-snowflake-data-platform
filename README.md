# NorthStar Commerce — Snowflake Data Engineering Platform

End-to-end cloud-native Data Engineering project built on Snowflake and dbt.

## Overview

NorthStar Commerce simulates an e-commerce data platform that ingests relational and semi-structured data, processes incremental changes, applies data-quality controls, and publishes analytics-ready dimensional models.

## Architecture

CSV / JSON
    ↓
Snowflake Internal Stage
    ↓
COPY INTO
    ↓
RAW
    ↓
Dynamic Tables
    ↓
SILVER
    ↓
dbt
    ↓
STAGING / INTERMEDIATE
    ↓
GOLD
    ↓
Dimensions / Facts / Analytics Marts

Additional platform capabilities:

- CDC with Snowflake Streams
- Event-driven processing with Triggered Tasks
- MERGE-based upserts
- Snowpark Python Data Quality
- Metadata-driven DQ framework
- dbt tests and lineage
- DEV / PROD environment separation
- Native Snowflake dbt deployment and orchestration

## Technology Stack

- Snowflake
- SQL
- dbt
- Snowpark Python
- Dynamic Tables
- Streams & Tasks
- JSON / VARIANT
- Git / GitHub

## dbt Architecture

### Staging
- `stg_customers`
- `stg_products`
- `stg_orders`
- `stg_web_events`

### Intermediate
- `int_valid_orders`

### Dimensions and Facts
- `dim_customer`
- `dim_product`
- `fact_orders`

### Analytics Marts
- `mart_sales_daily`
- `mart_customer_360`

## Data Quality

The platform contains two complementary quality layers:

1. Snowpark metadata-driven data-quality rules.
2. dbt model tests including:
   - unique
   - not_null
   - accepted_values
   - relationships

Invalid records are preserved upstream for traceability but prevented from reaching certified analytical fact models.

## Environments

Development:
`NORTHSTAR_DB.DBT_DEV`

Production transformations:
`NORTHSTAR_DB.DBT_TRANSFORM`

Analytics / Gold:
`NORTHSTAR_DB.GOLD`

## Status

🚧 Project in active development.