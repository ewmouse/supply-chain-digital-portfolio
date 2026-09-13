from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# A. 项目路径
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


# ============================================================
# B. 建立数据库连接
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

db_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url)


# ============================================================
# C. 读取四份CSV
# ============================================================

parts = pd.read_csv(
    RAW_DATA_DIR / "parts_master.csv"
)

history = pd.read_csv(
    RAW_DATA_DIR / "supply_chain_history.csv"
)

purchase_orders = pd.read_csv(
    RAW_DATA_DIR / "purchase_orders.csv"
)

quality = pd.read_csv(
    RAW_DATA_DIR / "quality_incidents.csv"
)


print("1. Raw data loaded.")

print("parts:", parts.shape)
print("history:", history.shape)
print("purchase_orders:", purchase_orders.shape)
print("quality:", quality.shape)


# ============================================================
# D. 类型转换
# ============================================================

history["date"] = pd.to_datetime(
    history["date"]
)

purchase_orders["order_date"] = pd.to_datetime(
    purchase_orders["order_date"]
)

purchase_orders["promised_date"] = pd.to_datetime(
    purchase_orders["promised_date"]
)

purchase_orders["receipt_date"] = pd.to_datetime(
    purchase_orders["receipt_date"]
)

quality["incident_date"] = pd.to_datetime(
    quality["incident_date"]
)


# 原始数据的 Yes / No 转成数据库真正的 Boolean
parts["is_repairable"] = parts["is_repairable"].map(
    {
        "Yes": True,
        "No": False,
    }
)


# shelf_life_days允许为空
parts["shelf_life_days"] = (
    pd.to_numeric(
        parts["shelf_life_days"],
        errors="coerce"
    )
    .astype("Int64")
)


print("2. Data types transformed.")


# ============================================================
# E. Data Validation
# ============================================================

# Part ID应该唯一
assert not parts["part_id"].duplicated().any(), \
    "Duplicate part_id found."


# PO ID应该唯一
assert not purchase_orders["po_id"].duplicated().any(), \
    "Duplicate po_id found."


# Quality Incident ID应该唯一
assert not quality["incident_id"].duplicated().any(), \
    "Duplicate incident_id found."


# Weekly Fact的业务主键应该唯一
weekly_key = [
    "date",
    "site_id",
    "part_id",
]

assert not history.duplicated(weekly_key).any(), \
    "Duplicate weekly business key found."


# 检查事实表里的Part是否全部存在于Master
master_parts = set(parts["part_id"])

assert set(history["part_id"]).issubset(master_parts), \
    "Unknown part found in supply history."

assert set(purchase_orders["part_id"]).issubset(master_parts), \
    "Unknown part found in PO."

assert set(quality["part_id"]).issubset(master_parts), \
    "Unknown part found in quality incidents."


# 检查Yes/No是否全部成功转换
assert parts["is_repairable"].notna().all(), \
    "Unknown is_repairable value found."


print("3. Data validation passed.")


# ============================================================
# F. 建立维度表
# ============================================================

dim_supplier = (
    parts[
        [
            "supplier_id_primary",
            "supplier_risk_class",
        ]
    ]
    .drop_duplicates()
    .rename(
        columns={
            "supplier_id_primary": "supplier_id"
        }
    )
    .sort_values("supplier_id")
)


all_sites = (
    set(history["site_id"])
    | set(purchase_orders["site_id"])
    | set(quality["site_id"])
)

dim_site = pd.DataFrame(
    {
        "site_id": sorted(all_sites)
    }
)


dim_part = parts[
    [
        "part_id",
        "part_family",
        "criticality_class",
        "unit_cost",
        "lead_time_days",
        "supplier_id_primary",
        "is_repairable",
        "shelf_life_days",
    ]
].copy()


print("4. Dimension tables prepared.")


# ============================================================
# G. 事实表
# ============================================================

fact_supply_weekly = history.copy()

fact_purchase_order = purchase_orders.copy()

fact_quality_incident = quality.copy()


print("5. Fact tables prepared.")


# ============================================================
# H. 打印入库前规模
# ============================================================

print("\nTables ready for database:")

print(
    "dim_supplier:",
    dim_supplier.shape
)

print(
    "dim_site:",
    dim_site.shape
)

print(
    "dim_part:",
    dim_part.shape
)

print(
    "fact_supply_weekly:",
    fact_supply_weekly.shape
)

print(
    "fact_purchase_order:",
    fact_purchase_order.shape
)

print(
    "fact_quality_incident:",
    fact_quality_incident.shape
)


# ============================================================
# I. 清空旧数据
# ============================================================

with engine.begin() as connection:

    connection.execute(
        text(
            """
            TRUNCATE TABLE
                fact_quality_incident,
                fact_purchase_order,
                fact_supply_weekly,
                dim_part,
                dim_site,
                dim_supplier
            CASCADE;
            """
        )
    )


print("\n6. Old database rows cleared.")


# ============================================================
# J. 按外键依赖顺序写入数据库
# ============================================================

dim_supplier.to_sql(
    "dim_supplier",
    engine,
    if_exists="append",
    index=False,
)

print("dim_supplier loaded.")


dim_site.to_sql(
    "dim_site",
    engine,
    if_exists="append",
    index=False,
)

print("dim_site loaded.")


dim_part.to_sql(
    "dim_part",
    engine,
    if_exists="append",
    index=False,
)

print("dim_part loaded.")


fact_supply_weekly.to_sql(
    "fact_supply_weekly",
    engine,
    if_exists="append",
    index=False,
    chunksize=5000,
)

print("fact_supply_weekly loaded.")


fact_purchase_order.to_sql(
    "fact_purchase_order",
    engine,
    if_exists="append",
    index=False,
    chunksize=5000,
)

print("fact_purchase_order loaded.")


fact_quality_incident.to_sql(
    "fact_quality_incident",
    engine,
    if_exists="append",
    index=False,
)

print("fact_quality_incident loaded.")


print("\n======================================")
print("ETL COMPLETED SUCCESSFULLY")
print("======================================")