{{ config(materialized='table') }}

select
    customer_id,
    first_name,
    last_name,
    email,
    country,
    signup_date,
    customer_status,
    is_email_present

from {{ ref('stg_customers') }}