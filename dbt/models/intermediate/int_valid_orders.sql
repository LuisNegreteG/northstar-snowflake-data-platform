with orders as (

    select *
    from {{ ref('stg_orders') }}

),

valid_orders as (

    select
        order_id,
        customer_id,
        product_id,
        order_date,
        quantity,
        unit_price,
        line_amount,
        order_status,
        source_file,
        ingested_at

    from orders

    where is_valid_order = true

)

select *
from valid_orders