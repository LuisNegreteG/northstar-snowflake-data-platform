{{ config(materialized='table') }}

with orders as (

    select *
    from {{ ref('fact_orders') }}

),

daily_sales as (

    select
        order_date,

        count(distinct order_id) as total_orders,
        count(distinct customer_id) as unique_customers,

        sum(quantity) as units_sold,
        sum(line_amount) as gross_revenue,

        gross_revenue / nullif(total_orders, 0) as avg_order_value

    from orders

    where order_status = 'COMPLETED'

    group by order_date

)

select *
from daily_sales