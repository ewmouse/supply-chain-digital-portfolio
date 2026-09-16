import os
import re

from dotenv import load_dotenv
from openai import OpenAI



load_dotenv()



client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


MODEL_NAME = os.getenv(
    "DEEPSEEK_MODEL",
    "deepseek-v4-flash",
)



SCHEMA_CONTEXT = """
You are a PostgreSQL expert for a supply chain analytics system.

Your job is to convert the user's natural-language question
into ONE safe PostgreSQL query.

Available analytical views:

1. vw_inventory_health

Important columns:
date
site_id
part_id
part_family
criticality_class
unit_cost
lead_time_days
supplier_id
consumption_qty
on_hand_qty
backorder_qty
blocked_qty
forecast_qty
avg_consumption_4w
available_inventory
demand_signal
coverage_weeks
lead_time_demand
shortage_gap_qty
excess_qty_candidate
inventory_status

inventory_status values:
CONFIRMED_SHORTAGE
SHORTAGE_RISK
BLOCKED_STOCK
EXCESS_CANDIDATE
NO_DEMAND_STOCK
HEALTHY


2. vw_supplier_performance

Important columns:
supplier_id
supplier_risk_class
po_count
on_time_pct
in_full_pct
otif_pct
fill_rate_pct
avg_late_days
quality_incident_count
critical_incident_count
supplied_part_count
critical_a_part_count
supplier_status


3. vw_exception_workbench

Important columns:
date
site_id
part_id
part_family
criticality_class
supplier_id
exception_type
priority
available_inventory
demand_signal
coverage_weeks
lead_time_weeks
lead_time_demand
backorder_qty
shortage_gap_qty
blocked_inventory_value
on_hand_inventory_value
otif_pct
fill_rate_pct
avg_late_days
critical_incident_count
supplier_status
suggested_action


Rules:

1. PostgreSQL only.
2. Return SQL only.
3. Only SELECT or WITH queries are allowed.
4. Never use INSERT, UPDATE, DELETE, DROP,
   ALTER, TRUNCATE, CREATE, GRANT or REVOKE.
5. Prefer the analytical views above.
6. Never invent tables or columns.
7. Do not output Markdown code fences.
8. Unless aggregation naturally returns few rows,
   use LIMIT 100.
"""



def clean_generated_sql(sql: str) -> str:

    sql = sql.strip()

    sql = re.sub(
        r"^```(?:sql)?",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = re.sub(
        r"```$",
        "",
        sql,
    )

    return sql.strip()




def validate_sql(sql: str) -> str:

    normalized = sql.strip().lower()

    if not (
        normalized.startswith("select")
        or normalized.startswith("with")
    ):

        raise ValueError(
            "Only SELECT or WITH queries are allowed."
        )


    forbidden_words = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
        "copy",
    ]


    for word in forbidden_words:

        if re.search(
            rf"\b{word}\b",
            normalized,
        ):

            raise ValueError(
                f"Forbidden SQL keyword: {word}"
            )


    sql = sql.rstrip(";").strip()


    if ";" in sql:

        raise ValueError(
            "Multiple SQL statements are not allowed."
        )


    return sql



def generate_sql(question: str) -> str:

    response = client.chat.completions.create(
        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": SCHEMA_CONTEXT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],

        temperature=0,
    )


    sql = (
        response
        .choices[0]
        .message
        .content
    )


    sql = clean_generated_sql(sql)

    return validate_sql(sql)