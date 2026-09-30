with source as (

    select *
    from {{ source('silver', 'orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        product_id,
        order_date,
        quantity,
        unit_price,
        line_amount,
        order_status,
        is_customer_valid,
        is_product_valid,
        is_quantity_valid,
        is_price_valid,
        is_valid_order,
        source_file,
        ingested_at

    from source

)

select *
from renamed