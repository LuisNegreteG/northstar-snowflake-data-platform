with source as (

    select *
    from {{ source('silver', 'products') }}

),

renamed as (

    select
        product_id,
        product_name,
        category,
        unit_price,
        is_active,
        source_file,
        ingested_at

    from source

)

select *
from renamed