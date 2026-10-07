# NorthStar Commerce — Architecture

NorthStar Commerce is an end-to-end modern data engineering platform built on Snowflake.

The project demonstrates how structured and semi-structured e-commerce data can be ingested, transformed, validated, modeled, orchestrated, and prepared for analytics using Snowflake-native capabilities, dbt, and Snowpark Python.

![NorthStar Commerce Architecture](./architecture.png)

---

## Architecture Overview

The platform follows this primary data flow:

```text
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
Analytics / Applications
```

Supporting capabilities include:

- Change Data Capture with Snowflake Streams
- Event-driven processing with triggered Tasks
- Scheduled dbt production execution
- Metadata-driven Data Quality with Snowpark Python
- DEV / PROD environment separation
- Git-based source control
- Reproducible synthetic datasets

---

## 1. Data Sources

The project uses synthetic e-commerce data across four business domains:

- Customers
- Products
- Orders
- Web events

Structured datasets are stored as CSV files, while behavioral event data is stored as JSON.

Two ingestion batches are included.

### Batch 1

Initial dataset used to populate the platform.

### Batch 2

Incremental dataset used to demonstrate:

- Incremental ingestion
- Dynamic Table refresh
- Downstream transformation updates
- Pipeline reproducibility

The source data intentionally contains quality issues so the Data Quality framework can be demonstrated.

Examples include:

- One customer with a missing email
- Inconsistent customer-status casing
- One order referencing a non-existent customer
- One order with quantity equal to zero

---

## 2. RAW Ingestion Layer

Source files are uploaded to the Snowflake internal stage:

`NORTHSTAR_DB.RAW.NORTHSTAR_STAGE`

Two Snowflake file formats are used:

- CSV
- JSON

Data is loaded with `COPY INTO` into four RAW tables:

- `NORTHSTAR_DB.RAW.RAW_CUSTOMERS`
- `NORTHSTAR_DB.RAW.RAW_PRODUCTS`
- `NORTHSTAR_DB.RAW.RAW_ORDERS`
- `NORTHSTAR_DB.RAW.RAW_WEB_EVENTS`

The ingestion process also captures Snowflake file metadata:

- `METADATA$FILENAME`
- `METADATA$START_SCAN_TIME`

This provides ingestion traceability and basic lineage information.

The RAW layer intentionally keeps the data close to its original source representation.

---

## 3. SILVER Processing Layer

The SILVER layer is implemented with Snowflake Dynamic Tables.

Main objects:

- `NORTHSTAR_DB.SILVER.CUSTOMERS`
- `NORTHSTAR_DB.SILVER.PRODUCTS`
- `NORTHSTAR_DB.SILVER.ORDERS`
- `NORTHSTAR_DB.SILVER.WEB_EVENTS`

Dynamic Tables are configured with:

```sql
TARGET_LAG = '5 minutes'
REFRESH_MODE = INCREMENTAL
```

The SILVER layer performs:

- String normalization
- Customer-status standardization
- Email normalization
- JSON parsing
- Relational extraction from VARIANT
- Customer validation
- Product validation
- Quantity validation
- Price validation
- Line-amount calculation
- Web-event completeness validation

Instead of immediately deleting invalid records, quality flags are added to the data.

Examples:

- `IS_EMAIL_PRESENT`
- `IS_CUSTOMER_VALID`
- `IS_PRODUCT_VALID`
- `IS_QUANTITY_VALID`
- `IS_PRICE_VALID`
- `IS_VALID_ORDER`
- `IS_EVENT_COMPLETE`

This keeps data-quality issues observable while allowing certified downstream models to exclude invalid records.

---

## 4. Change Data Capture

NorthStar includes an explicit CDC pipeline using Snowflake Streams and Tasks.

```text
CUSTOMER_CDC_SOURCE
        ↓
CUSTOMER_CDC_STREAM
        ↓
Triggered Snowflake Task
        ↓
MERGE
        ↓
CUSTOMER_CURRENT
```

The CDC implementation supports:

- INSERT
- UPDATE
- DELETE

Snowflake stream metadata is used to interpret each change:

- `METADATA$ACTION`
- `METADATA$ISUPDATE`

The triggered task runs when the stream contains new records and applies the changes into the current-state customer table using `MERGE`.

This demonstrates event-driven processing in addition to scheduled batch orchestration.

---

## 5. Data Quality Framework

NorthStar contains a metadata-driven Data Quality framework implemented with Snowpark Python.

Quality rules are stored in:

`NORTHSTAR_DB.CONTROL.DQ_RULES`

Each rule contains metadata such as:

- `RULE_ID`
- `DOMAIN`
- `TARGET_TABLE`
- `CHECK_NAME`
- `FAILURE_CONDITION`
- `SEVERITY`
- `ENABLED`

The Snowpark Data Quality engine dynamically retrieves enabled rules and executes them without requiring Python code changes for every new validation.

Historical execution results are stored in:

`NORTHSTAR_DB.CONTROL.DQ_RUN_RESULTS`

Configured checks include:

- Invalid order
- Invalid customer reference
- Invalid quantity
- Invalid price
- Missing order ID
- Missing customer email
- Invalid customer status
- Invalid web-event customer
- Incomplete web event

This design separates rule definition from execution and makes the framework extensible.

---

## 6. dbt Transformation Layer

dbt is used to create reusable analytical models on top of the Snowflake SILVER layer.

The project contains three logical modeling layers.

### Staging

Models:

- `stg_customers`
- `stg_products`
- `stg_orders`
- `stg_web_events`

Responsibilities:

- Source references
- Standardized column selection
- Light transformations
- Source-level Data Quality tests

### Intermediate

Model:

- `int_valid_orders`

Responsibilities:

- Reusable business logic
- Filtering invalid transactional records
- Preparing certified data for analytical models

### Marts

Dimensions:

- `dim_customer`
- `dim_product`

Fact:

- `fact_orders`

Analytics marts:

- `mart_sales_daily`
- `mart_customer_360`

The dbt project contains tests including:

- `unique`
- `not_null`
- `accepted_values`
- `relationships`

Known upstream anomalies can be configured as warnings while certified analytical relationships remain strict.

---

## 7. Development and Production Separation

The dbt project separates development and production schemas.

### Development

`NORTHSTAR_DB.DBT_DEV`

### Production Transformations

`NORTHSTAR_DB.DBT_TRANSFORM`

### Production Analytics

`NORTHSTAR_DB.GOLD`

A custom `generate_schema_name` macro controls schema routing depending on the selected dbt target.

This keeps development work isolated from production-facing models.

---

## 8. GOLD Analytics Layer

The GOLD layer contains analytics-ready dimensional and aggregate models.

### Dimensions

- `DIM_CUSTOMER`
- `DIM_PRODUCT`

### Fact

- `FACT_ORDERS`

### Analytics Marts

- `MART_SALES_DAILY`
- `MART_CUSTOMER_360`

`MART_SALES_DAILY` provides metrics such as:

- Total orders
- Unique customers
- Units sold
- Gross revenue
- Average order value

`MART_CUSTOMER_360` combines customer, transactional, and behavioral information including:

- Total orders
- Completed orders
- Lifetime revenue
- Last order date
- Total web events
- Product views
- Add-to-cart events
- Purchase events
- Last event timestamp

---

## 9. dbt Deployment and Orchestration

The dbt project is deployed as a native Snowflake DBT PROJECT object:

`NORTHSTAR_DB.CONTROL.NORTHSTAR_DBT_PROJECT`

Production builds can be executed using:

```sql
EXECUTE DBT PROJECT
    NORTHSTAR_DB.CONTROL.NORTHSTAR_DBT_PROJECT
    ARGS = 'build --target prod';
```

A Snowflake Task is also configured for scheduled production execution:

`NORTHSTAR_DB.CONTROL.NORTHSTAR_DBT_PROD_TASK`

The portfolio version keeps the task suspended by default to avoid unnecessary compute consumption.

The platform therefore demonstrates both:

- Event-driven execution through Streams and triggered Tasks
- Scheduled execution through the production dbt Task

---

## 10. Analytics Consumption

The GOLD models are designed to support downstream analytical applications.

The final planned consumption layer is a Streamlit application in Snowflake.

Planned capabilities include:

- Sales KPIs
- Revenue trends
- Customer insights
- Product performance
- Data Quality monitoring

This keeps the analytical experience inside the Snowflake ecosystem.

---

## Validated Project Results

After loading both sample-data batches:

```text
RAW_CUSTOMERS  = 11
RAW_PRODUCTS   = 9
RAW_ORDERS     = 23
RAW_WEB_EVENTS = 19
```

After Data Quality filtering:

```text
FACT_ORDERS = 21
```

Two intentionally invalid orders are excluded:

```text
ORDER 5016 → invalid customer reference
ORDER 5017 → quantity = 0
```

Validated analytical results:

```text
Completed Orders = 17
Units Sold       = 23
Gross Revenue    = 2709.77
Average Order Value ≈ 159.40
```

Average Order Value:

```text
2709.77 / 17 = 159.398...
```

---

## Key Engineering Concepts Demonstrated

This project demonstrates practical implementation of:

- Snowflake cloud data engineering
- ELT architecture
- Structured and semi-structured ingestion
- Internal stages
- `COPY INTO`
- JSON and VARIANT processing
- Dynamic Tables
- Incremental processing
- Data lineage metadata
- Data Quality flags
- Snowpark Python
- Metadata-driven validation
- Snowflake Streams
- Change Data Capture
- Triggered Tasks
- `MERGE`-based synchronization
- dbt modeling
- dbt testing
- Dimensional modeling
- DEV / PROD separation
- Native dbt deployment
- Scheduled orchestration
- Git / GitHub integration
- Reproducible sample datasets
- Analytics-ready data marts

---

## Repository Structure

```text
northstar-snowflake-data-platform/
│
├── sample_data/
│   └── Synthetic CSV and JSON source datasets
│
├── snowflake/
│   ├── 01_setup/
│   ├── 02_ingestion/
│   ├── 03_dynamic_tables/
│   ├── 04_cdc/
│   └── 05_orchestration/
│
├── snowpark/
│   └── data_quality/
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── macros/
│
└── docs/
    └── architecture/
        ├── architecture.md
        └── architecture.png
```

---

## Design Goal

NorthStar Commerce is intentionally portfolio-sized while demonstrating patterns that can scale to larger production data platforms.

The project emphasizes:

**reproducibility, incremental processing, explicit Data Quality, modular transformations, environment separation, orchestration, and analytics-ready delivery.**