"""
NorthStar Commerce
Metadata-driven Data Quality Engine

Runs enabled quality rules stored in:
    NORTHSTAR_DB.CONTROL.DQ_RULES

Persists historical results to:
    NORTHSTAR_DB.CONTROL.DQ_RUN_RESULTS
"""

from uuid import uuid4

from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import current_timestamp


session = get_active_session()


# ------------------------------------------------------------
# Load active rules
# ------------------------------------------------------------

rules = session.sql(
    """
    SELECT
        RULE_ID,
        DOMAIN,
        TARGET_TABLE,
        CHECK_NAME,
        FAILURE_CONDITION,
        SEVERITY
    FROM NORTHSTAR_DB.CONTROL.DQ_RULES
    WHERE ENABLED = TRUE
    ORDER BY RULE_ID
    """
).collect()


run_id = str(uuid4())
results = []


# ------------------------------------------------------------
# Execute rules
# ------------------------------------------------------------

for rule in rules:

    query = f"""
        SELECT COUNT(*) AS FAILED_ROWS
        FROM {rule["TARGET_TABLE"]}
        WHERE {rule["FAILURE_CONDITION"]}
    """

    failed_rows = (
        session.sql(query)
        .collect()[0]["FAILED_ROWS"]
    )

    status = "PASS" if failed_rows == 0 else "FAIL"

    results.append(
        (
            run_id,
            rule["RULE_ID"],
            rule["DOMAIN"],
            rule["TARGET_TABLE"],
            rule["CHECK_NAME"],
            rule["SEVERITY"],
            failed_rows,
            status,
        )
    )


# ------------------------------------------------------------
# Persist results
# ------------------------------------------------------------

run_results = session.create_dataframe(
    results,
    schema=[
        "RUN_ID",
        "RULE_ID",
        "DOMAIN",
        "TARGET_TABLE",
        "CHECK_NAME",
        "SEVERITY",
        "FAILED_ROWS",
        "STATUS",
    ],
)

run_results = run_results.with_column(
    "CHECKED_AT",
    current_timestamp(),
)

run_results.write.mode("append").save_as_table(
    "NORTHSTAR_DB.CONTROL.DQ_RUN_RESULTS"
)


# ------------------------------------------------------------
# Execution summary
# ------------------------------------------------------------

print(f"DQ Run ID: {run_id}")
print(f"Rules executed: {len(results)}")

run_results.show()