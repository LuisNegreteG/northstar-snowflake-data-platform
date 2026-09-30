with source as (

    select *
    from {{ source('silver', 'customers') }}

),

renamed as (

    select
        customer_id,
        first_name,
        last_name,
        email,
        country,
        signup_date,
        customer_status,
        is_email_present,
        source_file,
        ingested_at

    from source

)

select *
from renamed