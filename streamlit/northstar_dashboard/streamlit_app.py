import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NorthStar Commerce",
    page_icon="❄️",
    layout="wide",
)


# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

session = st.connection("snowflake").session()


@st.cache_data(ttl=300)
def run_query(query: str):
    """
    Execute a Snowflake query and cache the result
    for 5 minutes.
    """
    return session.sql(query).to_pandas()


# ============================================================
# DATA LOADERS
# ============================================================

# ------------------------------------------------------------
# Sales
# Source: GOLD.MART_SALES_DAILY
# ------------------------------------------------------------

sales = run_query(
    """
    SELECT
        ORDER_DATE,
        TOTAL_ORDERS,
        UNIQUE_CUSTOMERS,
        UNITS_SOLD,
        GROSS_REVENUE,
        AVG_ORDER_VALUE
    FROM NORTHSTAR_DB.GOLD.MART_SALES_DAILY
    ORDER BY ORDER_DATE
    """
)


# ------------------------------------------------------------
# Customer 360
# Source: GOLD.MART_CUSTOMER_360
# ------------------------------------------------------------

customers = run_query(
    """
    SELECT
        CUSTOMER_ID,
        FIRST_NAME,
        LAST_NAME,
        EMAIL,
        COUNTRY,
        CUSTOMER_STATUS,
        TOTAL_ORDERS,
        COMPLETED_ORDERS,
        LIFETIME_REVENUE,
        LAST_ORDER_DATE,
        TOTAL_WEB_EVENTS,
        PRODUCT_VIEWS,
        ADD_TO_CART_EVENTS,
        PURCHASE_EVENTS,
        LAST_EVENT_TS
    FROM NORTHSTAR_DB.GOLD.MART_CUSTOMER_360
    ORDER BY LIFETIME_REVENUE DESC
    """
)


# ------------------------------------------------------------
# Product Performance
# Derived from GOLD.FACT_ORDERS + GOLD.DIM_PRODUCT
# ------------------------------------------------------------

products = run_query(
    """
    SELECT
        p.PRODUCT_ID,
        p.PRODUCT_NAME,
        p.CATEGORY,

        COUNT(DISTINCT f.ORDER_ID) AS TOTAL_ORDERS,

        SUM(f.QUANTITY) AS UNITS_SOLD,

        SUM(f.LINE_AMOUNT) AS GROSS_REVENUE,

        SUM(f.LINE_AMOUNT)
            / NULLIF(COUNT(DISTINCT f.ORDER_ID), 0)
            AS AVG_ORDER_VALUE

    FROM NORTHSTAR_DB.GOLD.FACT_ORDERS f

    INNER JOIN NORTHSTAR_DB.GOLD.DIM_PRODUCT p
        ON f.PRODUCT_ID = p.PRODUCT_ID

    WHERE f.ORDER_STATUS = 'COMPLETED'

    GROUP BY
        p.PRODUCT_ID,
        p.PRODUCT_NAME,
        p.CATEGORY

    ORDER BY GROSS_REVENUE DESC
    """
)


# ------------------------------------------------------------
# Latest Data Quality Run
# Source: CONTROL.DQ_RUN_RESULTS
# ------------------------------------------------------------

dq = run_query(
    """
    SELECT
        RULE_ID,
        DOMAIN,
        TARGET_TABLE,
        CHECK_NAME,
        SEVERITY,
        FAILED_ROWS,
        STATUS,
        CHECKED_AT

    FROM NORTHSTAR_DB.CONTROL.DQ_RUN_RESULTS

    WHERE RUN_ID = (
        SELECT RUN_ID
        FROM NORTHSTAR_DB.CONTROL.DQ_RUN_RESULTS
        GROUP BY RUN_ID
        ORDER BY MAX(CHECKED_AT) DESC
        LIMIT 1
    )

    ORDER BY
        CASE SEVERITY
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH' THEN 2
            WHEN 'MEDIUM' THEN 3
            ELSE 4
        END,
        RULE_ID
    """
)


# ============================================================
# DATA PREPARATION
# ============================================================

sales["ORDER_DATE"] = pd.to_datetime(
    sales["ORDER_DATE"]
)

customers["FULL_NAME"] = (
    customers["FIRST_NAME"].fillna("")
    + " "
    + customers["LAST_NAME"].fillna("")
).str.strip()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("❄️ NorthStar")

    st.caption(
        "End-to-End Snowflake Data Platform"
    )

    st.divider()

    st.markdown("### Data Platform")

    st.markdown(
        """
**Warehouse:** Snowflake  
**Transformation:** dbt  
**Processing:** Snowpark Python  
**CDC:** Streams + Tasks  
**Data Quality:** Metadata-driven
        """
    )

    st.divider()

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()

    st.caption(
        "Queries cached for 5 minutes."
    )


# ============================================================
# HEADER
# ============================================================

st.title("❄️ NorthStar Commerce")

st.markdown(
    """
**Analytics layer for the NorthStar Snowflake Data Platform**

Monitoring commercial performance, customer behavior,
product performance, and Data Quality from certified
Snowflake models.
    """
)

st.divider()


# ============================================================
# TABS
# ============================================================

overview_tab, customer_tab, product_tab, dq_tab = st.tabs(
    [
        "📊 Sales Overview",
        "👥 Customer 360",
        "📦 Product Performance",
        "✅ Data Quality",
    ]
)


# ============================================================
# SALES OVERVIEW
# ============================================================

with overview_tab:

    st.subheader("Sales Performance")

    min_date = sales["ORDER_DATE"].min().date()
    max_date = sales["ORDER_DATE"].max().date()

    selected_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(selected_dates) == 2:

        start_date, end_date = selected_dates

        filtered_sales = sales[
            (
                sales["ORDER_DATE"].dt.date
                >= start_date
            )
            &
            (
                sales["ORDER_DATE"].dt.date
                <= end_date
            )
        ].copy()

    else:

        filtered_sales = sales.copy()


    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    total_orders = int(
        filtered_sales["TOTAL_ORDERS"].sum()
    )

    units_sold = int(
        filtered_sales["UNITS_SOLD"].sum()
    )

    gross_revenue = float(
        filtered_sales["GROSS_REVENUE"].sum()
    )

    average_order_value = (
        gross_revenue / total_orders
        if total_orders > 0
        else 0
    )


    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric(
        "Completed Orders",
        f"{total_orders:,}",
    )

    kpi2.metric(
        "Units Sold",
        f"{units_sold:,}",
    )

    kpi3.metric(
        "Gross Revenue",
        f"${gross_revenue:,.2f}",
    )

    kpi4.metric(
        "Average Order Value",
        f"${average_order_value:,.2f}",
    )

    st.divider()


    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    left, right = st.columns(2)

    with left:

        st.markdown("#### Revenue Trend")

        revenue_chart = (
            filtered_sales[
                [
                    "ORDER_DATE",
                    "GROSS_REVENUE",
                ]
            ]
            .set_index("ORDER_DATE")
        )

        st.line_chart(
            revenue_chart,
            use_container_width=True,
        )


    with right:

        st.markdown("#### Orders by Day")

        order_chart = (
            filtered_sales[
                [
                    "ORDER_DATE",
                    "TOTAL_ORDERS",
                ]
            ]
            .set_index("ORDER_DATE")
        )

        st.bar_chart(
            order_chart,
            use_container_width=True,
        )


    # --------------------------------------------------------
    # DAILY SALES TABLE
    # --------------------------------------------------------

    st.markdown("#### Daily Sales Detail")

    display_sales = filtered_sales.copy()

    display_sales["ORDER_DATE"] = (
        display_sales["ORDER_DATE"].dt.date
    )

    st.dataframe(
        display_sales,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ORDER_DATE":
                st.column_config.DateColumn(
                    "Order Date"
                ),

            "TOTAL_ORDERS":
                st.column_config.NumberColumn(
                    "Orders"
                ),

            "UNIQUE_CUSTOMERS":
                st.column_config.NumberColumn(
                    "Customers"
                ),

            "UNITS_SOLD":
                st.column_config.NumberColumn(
                    "Units Sold"
                ),

            "GROSS_REVENUE":
                st.column_config.NumberColumn(
                    "Gross Revenue",
                    format="$%.2f",
                ),

            "AVG_ORDER_VALUE":
                st.column_config.NumberColumn(
                    "Average Order Value",
                    format="$%.2f",
                ),
        },
    )


# ============================================================
# CUSTOMER 360
# ============================================================

with customer_tab:

    st.subheader("Customer 360")

    total_customers = len(customers)

    customers_with_orders = int(
        (
            customers["TOTAL_ORDERS"] > 0
        ).sum()
    )

    customer_revenue = float(
        customers["LIFETIME_REVENUE"]
        .fillna(0)
        .sum()
    )

    customers_with_activity = int(
        (
            customers["TOTAL_WEB_EVENTS"] > 0
        ).sum()
    )


    # --------------------------------------------------------
    # CUSTOMER KPIs
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Customers",
        f"{total_customers:,}",
    )

    c2.metric(
        "Customers with Orders",
        f"{customers_with_orders:,}",
    )

    c3.metric(
        "Lifetime Revenue",
        f"${customer_revenue:,.2f}",
    )

    c4.metric(
        "Customers with Web Activity",
        f"{customers_with_activity:,}",
    )

    st.divider()


    # --------------------------------------------------------
    # CUSTOMER CHARTS
    # --------------------------------------------------------

    left, right = st.columns(2)


    with left:

        st.markdown(
            "#### Top Customers by Revenue"
        )

        top_customers = (
            customers[
                [
                    "FULL_NAME",
                    "LIFETIME_REVENUE",
                ]
            ]
            .sort_values(
                "LIFETIME_REVENUE",
                ascending=False,
            )
            .head(10)
            .set_index("FULL_NAME")
        )

        st.bar_chart(
            top_customers,
            use_container_width=True,
        )


    with right:

        st.markdown(
            "#### Customer Engagement"
        )

        engagement = (
            customers[
                [
                    "FULL_NAME",
                    "TOTAL_WEB_EVENTS",
                ]
            ]
            .sort_values(
                "TOTAL_WEB_EVENTS",
                ascending=False,
            )
            .head(10)
            .set_index("FULL_NAME")
        )

        st.bar_chart(
            engagement,
            use_container_width=True,
        )


    # --------------------------------------------------------
    # CUSTOMER DETAIL
    # --------------------------------------------------------

    st.markdown("#### Customer Detail")

    customer_detail = customers[
        [
            "CUSTOMER_ID",
            "FULL_NAME",
            "COUNTRY",
            "CUSTOMER_STATUS",
            "TOTAL_ORDERS",
            "COMPLETED_ORDERS",
            "LIFETIME_REVENUE",
            "TOTAL_WEB_EVENTS",
            "PRODUCT_VIEWS",
            "ADD_TO_CART_EVENTS",
            "PURCHASE_EVENTS",
            "LAST_ORDER_DATE",
        ]
    ]


    st.dataframe(
        customer_detail,
        use_container_width=True,
        hide_index=True,
        column_config={
            "CUSTOMER_ID":
                st.column_config.NumberColumn(
                    "Customer ID"
                ),

            "FULL_NAME":
                st.column_config.TextColumn(
                    "Customer"
                ),

            "CUSTOMER_STATUS":
                st.column_config.TextColumn(
                    "Status"
                ),

            "TOTAL_ORDERS":
                st.column_config.NumberColumn(
                    "Orders"
                ),

            "COMPLETED_ORDERS":
                st.column_config.NumberColumn(
                    "Completed"
                ),

            "LIFETIME_REVENUE":
                st.column_config.NumberColumn(
                    "Lifetime Revenue",
                    format="$%.2f",
                ),

            "TOTAL_WEB_EVENTS":
                st.column_config.NumberColumn(
                    "Web Events"
                ),

            "PRODUCT_VIEWS":
                st.column_config.NumberColumn(
                    "Product Views"
                ),

            "ADD_TO_CART_EVENTS":
                st.column_config.NumberColumn(
                    "Add to Cart"
                ),

            "PURCHASE_EVENTS":
                st.column_config.NumberColumn(
                    "Purchases"
                ),
        },
    )


# ============================================================
# PRODUCT PERFORMANCE
# ============================================================

with product_tab:

    st.subheader("Product Performance")

    product_revenue = float(
        products["GROSS_REVENUE"]
        .fillna(0)
        .sum()
    )

    product_units = int(
        products["UNITS_SOLD"]
        .fillna(0)
        .sum()
    )

    number_products = len(products)

    top_product = (
        products.iloc[0]["PRODUCT_NAME"]
        if not products.empty
        else "N/A"
    )


    # --------------------------------------------------------
    # PRODUCT KPIs
    # --------------------------------------------------------

    p1, p2, p3, p4 = st.columns(4)

    p1.metric(
        "Products Sold",
        f"{number_products:,}",
    )

    p2.metric(
        "Units Sold",
        f"{product_units:,}",
    )

    p3.metric(
        "Revenue",
        f"${product_revenue:,.2f}",
    )

    p4.metric(
        "Top Product",
        top_product,
    )

    st.divider()


    # --------------------------------------------------------
    # PRODUCT CHART
    # --------------------------------------------------------

    st.markdown(
        "#### Revenue by Product"
    )

    product_chart = (
        products[
            [
                "PRODUCT_NAME",
                "GROSS_REVENUE",
            ]
        ]
        .set_index("PRODUCT_NAME")
    )

    st.bar_chart(
        product_chart,
        use_container_width=True,
    )


    # --------------------------------------------------------
    # PRODUCT TABLE
    # --------------------------------------------------------

    st.markdown(
        "#### Product Detail"
    )

    st.dataframe(
        products,
        use_container_width=True,
        hide_index=True,
        column_config={
            "PRODUCT_ID":
                st.column_config.NumberColumn(
                    "Product ID"
                ),

            "PRODUCT_NAME":
                st.column_config.TextColumn(
                    "Product"
                ),

            "CATEGORY":
                st.column_config.TextColumn(
                    "Category"
                ),

            "TOTAL_ORDERS":
                st.column_config.NumberColumn(
                    "Orders"
                ),

            "UNITS_SOLD":
                st.column_config.NumberColumn(
                    "Units Sold"
                ),

            "GROSS_REVENUE":
                st.column_config.NumberColumn(
                    "Gross Revenue",
                    format="$%.2f",
                ),

            "AVG_ORDER_VALUE":
                st.column_config.NumberColumn(
                    "Average Order Value",
                    format="$%.2f",
                ),
        },
    )


# ============================================================
# DATA QUALITY
# ============================================================

with dq_tab:

    st.subheader("Data Quality Monitoring")


    if dq.empty:

        st.info(
            "No Data Quality execution results "
            "are currently available."
        )

    else:

        total_rules = len(dq)

        passed_rules = int(
            (
                dq["STATUS"] == "PASS"
            ).sum()
        )

        failed_rules = int(
            (
                dq["STATUS"] == "FAIL"
            ).sum()
        )

        failed_rows = int(
            dq["FAILED_ROWS"]
            .fillna(0)
            .sum()
        )


        # ----------------------------------------------------
        # DATA QUALITY KPIs
        # ----------------------------------------------------

        q1, q2, q3, q4 = st.columns(4)

        q1.metric(
            "Rules Executed",
            f"{total_rules:,}",
        )

        q2.metric(
            "Passed",
            f"{passed_rules:,}",
        )

        q3.metric(
            "Failed",
            f"{failed_rules:,}",
        )

        q4.metric(
            "Failed Rows",
            f"{failed_rows:,}",
        )

        st.divider()


        # ----------------------------------------------------
        # LATEST RUN
        # ----------------------------------------------------

        st.markdown(
            "#### Latest Data Quality Run"
        )

        latest_run_time = (
            pd.to_datetime(
                dq["CHECKED_AT"]
            ).max()
        )

        if pd.notna(latest_run_time):

            st.caption(
                f"Latest execution: "
                f"{latest_run_time}"
            )


        st.dataframe(
            dq[
                [
                    "DOMAIN",
                    "CHECK_NAME",
                    "SEVERITY",
                    "FAILED_ROWS",
                    "STATUS",
                    "CHECKED_AT",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "DOMAIN":
                    st.column_config.TextColumn(
                        "Domain"
                    ),

                "CHECK_NAME":
                    st.column_config.TextColumn(
                        "Check"
                    ),

                "SEVERITY":
                    st.column_config.TextColumn(
                        "Severity"
                    ),

                "FAILED_ROWS":
                    st.column_config.NumberColumn(
                        "Failed Rows"
                    ),

                "STATUS":
                    st.column_config.TextColumn(
                        "Status"
                    ),
            },
        )


        # ----------------------------------------------------
        # FAILED RULES
        # ----------------------------------------------------

        failing_rules = dq[
            dq["STATUS"] == "FAIL"
        ]

        if failing_rules.empty:

            st.success(
                "All Data Quality rules passed."
            )

        else:

            st.warning(
                f"{len(failing_rules)} Data Quality "
                "rule(s) detected issues. "
                "Affected records remain observable "
                "in upstream layers while certified "
                "analytical models can exclude "
                "invalid records."
            )

            st.markdown(
                "#### Rules Requiring Attention"
            )

            st.dataframe(
                failing_rules[
                    [
                        "DOMAIN",
                        "CHECK_NAME",
                        "SEVERITY",
                        "FAILED_ROWS",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NorthStar Commerce | "
    "Snowflake • dbt • Snowpark • "
    "Dynamic Tables • Streams • Tasks"
)