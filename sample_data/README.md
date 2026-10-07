# Sample data

Synthetic e-commerce data used by the NorthStar Commerce portfolio project.

## Batch 1
- customers.csv
- products.csv
- orders.csv
- web_events.json

Intentional quality issues:
- one customer with a missing email
- inconsistent customer status casing
- one order referencing a non-existent customer
- one order with quantity = 0

## Batch 2
- customers_batch2.csv
- products_batch2.csv
- orders_batch2.csv
- web_events_batch2.json

Batch 2 demonstrates incremental ingestion and Dynamic Table refresh behavior.

## Loading
Upload these files to:
`@NORTHSTAR_DB.RAW.NORTHSTAR_STAGE`

Then run:
`snowflake/02_ingestion/load_raw_data.sql`