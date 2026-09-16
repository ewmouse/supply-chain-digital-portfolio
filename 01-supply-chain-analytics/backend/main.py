from fastapi import FastAPI

from pydantic import BaseModel

from backend.database import (
    fetch_all,
    fetch_one,
    execute_readonly_query,
)

from backend.text_to_sql import (
    generate_sql,
)

from pathlib import Path

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.database import fetch_all, fetch_one

app = FastAPI(
    title="Supply Chain Analytics API",
    version="1.0.0",
)

class AskRequest(
    BaseModel
):

    question: str


FRONTEND_DIR = (
    Path(__file__).resolve().parents[1]
    / "frontend"
)


app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


@app.get("/")
def root():

    return {
        "message": "Supply Chain Analytics API is running."
    }


@app.get("/api/health")
def health_check():

    result = fetch_one(
        """
        SELECT
            current_database() AS database_name,
            CURRENT_TIMESTAMP AS server_time;
        """
    )

    return {
        "status": "ok",
        "database": result,
    }


@app.get("/api/overview")
def get_overview():

    result = fetch_one(
        """
        WITH latest AS (
            SELECT MAX(date) AS snapshot_date
            FROM vw_inventory_health
        )
        SELECT
            l.snapshot_date,
            COUNT(*) AS total_part_site,
            COUNT(*) FILTER (
                WHERE v.inventory_status <> 'HEALTHY'
            ) AS exception_count,
            COUNT(*) FILTER (
                WHERE v.inventory_status = 'CONFIRMED_SHORTAGE'
            ) AS confirmed_shortage_count,
            COUNT(*) FILTER (
                WHERE v.inventory_status = 'SHORTAGE_RISK'
            ) AS shortage_risk_count,
            COUNT(*) FILTER (
                WHERE v.inventory_status = 'EXCESS_CANDIDATE'
            ) AS excess_candidate_count,
            ROUND(
                SUM(v.on_hand_inventory_value),
                2
            ) AS inventory_value,
            ROUND(
                SUM(v.blocked_inventory_value),
                2
            ) AS blocked_inventory_value
        FROM vw_inventory_health AS v
        CROSS JOIN latest AS l
        WHERE v.date = l.snapshot_date
        GROUP BY l.snapshot_date;
        """
    )

    return result


@app.get("/api/exceptions")
def get_exceptions(
    priority: str | None = None,
    site_id: str | None = None,
    exception_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):

    conditions = []
    params = {
        "limit": limit
    }

    if priority:
        conditions.append(
            "priority = :priority"
        )
        params["priority"] = priority

    if site_id:
        conditions.append(
            "site_id = :site_id"
        )
        params["site_id"] = site_id

    if exception_type:
        conditions.append(
            "exception_type = :exception_type"
        )
        params["exception_type"] = exception_type


    where_clause = ""

    if conditions:

        where_clause = (
            "WHERE "
            + " AND ".join(conditions)
        )


    query = f"""
        SELECT
            date,
            priority,
            site_id,
            part_id,
            part_family,
            criticality_class,
            supplier_id,
            exception_type,
            available_inventory,
            demand_signal,
            coverage_weeks,
            shortage_gap_qty,
            otif_pct,
            supplier_status,
            suggested_action
        FROM vw_exception_workbench
        {where_clause}
        ORDER BY
            CASE priority
                WHEN 'P1' THEN 1
                WHEN 'P2' THEN 2
                ELSE 3
            END,
            criticality_class,
            shortage_gap_qty DESC
        LIMIT :limit;
    """

    return fetch_all(
        query,
        params,
    )

@app.get("/api/suppliers")
def get_suppliers():

    return fetch_all(
        """
        SELECT
            supplier_id,
            supplier_risk_class,
            po_count,
            on_time_pct,
            in_full_pct,
            otif_pct,
            fill_rate_pct,
            avg_late_days,
            quality_incident_count,
            critical_incident_count,
            critical_a_part_count,
            supplier_status
        FROM vw_supplier_performance
        ORDER BY
            CASE supplier_status
                WHEN 'QUALITY_ALERT' THEN 1
                WHEN 'DELIVERY_RISK' THEN 2
                WHEN 'WATCH' THEN 3
                ELSE 4
            END,
            otif_pct ASC;
        """
    )


@app.get(
    "/dashboard",
    include_in_schema=False,
)
def dashboard():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


@app.get("/api/sites")
def get_sites():

    rows = fetch_all(
        """
        SELECT site_id
        FROM dim_site
        ORDER BY site_id;
        """
    )

    return {
        "sites": [
            row["site_id"]
            for row in rows
        ]
    }

@app.get("/api/parts/{part_id}")
def get_part_detail(
    part_id: str,
    site_id: str,
):

    params = {
        "part_id": part_id,
        "site_id": site_id,
    }


    master = fetch_one(
        """
        SELECT
            part_id,
            part_family,
            criticality_class,
            unit_cost,
            lead_time_days,
            supplier_id_primary,
            is_repairable,
            shelf_life_days
        FROM dim_part
        WHERE part_id = :part_id;
        """,
        params,
    )


    if master is None:

        raise HTTPException(
            status_code=404,
            detail="Part not found.",
        )


    current = fetch_one(
        """
        SELECT
            date,
            site_id,
            part_id,
            available_inventory,
            demand_signal,
            coverage_weeks,
            lead_time_weeks,
            lead_time_demand,
            backorder_qty,
            blocked_qty,
            shortage_gap_qty,
            excess_qty_candidate,
            inventory_status
        FROM vw_inventory_health
        WHERE part_id = :part_id
          AND site_id = :site_id
        ORDER BY date DESC
        LIMIT 1;
        """,
        params,
    )


    history = fetch_all(
        """
        SELECT
            date,
            consumption_qty,
            forecast_qty,
            on_hand_qty,
            available_inventory,
            backorder_qty,
            coverage_weeks,
            inventory_status
        FROM vw_inventory_health
        WHERE part_id = :part_id
          AND site_id = :site_id
        ORDER BY date DESC
        LIMIT 26;
        """,
        params,
    )


    purchase_orders = fetch_all(
        """
        SELECT
            po_id,
            supplier_id,
            order_date,
            promised_date,
            receipt_date,
            ordered_qty,
            received_qty,
            receipt_date
                - promised_date
                AS delay_days
        FROM fact_purchase_order
        WHERE part_id = :part_id
          AND site_id = :site_id
        ORDER BY order_date DESC
        LIMIT 10;
        """,
        params,
    )


    supplier = fetch_one(
        """
        SELECT
            supplier_id,
            supplier_risk_class,
            otif_pct,
            fill_rate_pct,
            avg_late_days,
            quality_incident_count,
            critical_incident_count,
            supplier_status
        FROM vw_supplier_performance
        WHERE supplier_id = :supplier_id;
        """,
        {
            "supplier_id":
                master[
                    "supplier_id_primary"
                ]
        },
    )


    return {
        "master": master,
        "current": current,
        "history": history,
        "purchase_orders":
            purchase_orders,
        "supplier": supplier,
    }


@app.post("/api/ask")
def ask_supply_chain(
    request: AskRequest
):

    try:

        
        generated_sql = (
            generate_sql(
                request.question
            )
        )


        
        rows = (
            execute_readonly_query(
                generated_sql
            )
        )


        
        columns = []

        if rows:

            columns = list(
                rows[0].keys()
            )


        
        return {
            "question":
                request.question,

            "sql":
                generated_sql,

            "columns":
                columns,

            "row_count":
                len(rows),

            "rows":
                rows,
        }


    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Text-to-SQL failed: "
                + str(error)
            ),
        )