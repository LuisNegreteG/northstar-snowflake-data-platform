{{ config(materialized='table') }}

with customers as (

    select *
    from {{ ref('dim_customer') }}

),

orders as (

    select *
    from {{ ref('fact_orders') }}

),

events as (

    select *
    from {{ ref('stg_web_events') }}

),

order_metrics as (

    select
        customer_id,

        count(distinct order_id) as total_orders,

        count(distinct case
            when order_status = 'COMPLETED'
            then order_id
        end) as completed_orders,

        sum(case
            when order_status = 'COMPLETED'
            then line_amount
            else 0
        end) as lifetime_revenue,

        max(order_date) as last_order_date

    from orders

    group by customer_id

),

event_metrics as (

    select
        customer_id,

        count(*) as total_web_events,

        count_if(event_type = 'product_view') as product_views,

        count_if(event_type = 'add_to_cart') as add_to_cart_events,

        count_if(event_type = 'purchase') as purchase_events,

        max(event_ts) as last_event_ts

    from events

    group by customer_id

)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.country,
    c.signup_date,
    c.customer_status,

    coalesce(o.total_orders, 0) as total_orders,
    coalesce(o.completed_orders, 0) as completed_orders,
    coalesce(o.lifetime_revenue, 0) as lifetime_revenue,
    o.last_order_date,

    coalesce(e.total_web_events, 0) as total_web_events,
    coalesce(e.product_views, 0) as product_views,
    coalesce(e.add_to_cart_events, 0) as add_to_cart_events,
    coalesce(e.purchase_events, 0) as purchase_events,
    e.last_event_ts

from customers c

left join order_metrics o
    on c.customer_id = o.customer_id

left join event_metrics e
    on c.customer_id = e.customer_id