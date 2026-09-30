{{ config(materialized='table') }}

select
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    line_amount,
    order_status

from {{ ref('int_valid_orders') }}