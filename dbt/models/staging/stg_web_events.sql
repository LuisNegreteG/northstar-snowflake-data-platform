with source as (

    select *
    from {{ source('silver', 'web_events') }}

),

renamed as (

    select
        event_id,
        customer_id,
        event_type,
        event_ts,
        device_type,
        device_os,
        product_id,
        order_id,
        search_query,
        cart_items,
        cart_value,
        is_customer_valid,
        is_event_complete,
        source_file,
        ingested_at

    from source

)

select *
from renamed