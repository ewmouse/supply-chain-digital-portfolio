CREATE OR REPLACE VIEW vw_inventory_health AS
WITH base AS (
    SELECT
        f.date,
        f.site_id,
        f.part_id,
        p.part_family,
        p.criticality_class,
        p.unit_cost,
        p.lead_time_days,
        p.supplier_id_primary AS supplier_id,
        f.planned_maintenance,
        f.consumption_qty,
        f.on_hand_qty,
        f.backorder_qty,
        f.blocked_qty,
        f.forecast_qty,
        f.forecast_type,
        f.forecast_uplift_pct,
        AVG(f.consumption_qty::numeric) OVER (
            PARTITION BY f.site_id, f.part_id
            ORDER BY f.date
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS avg_consumption_4w
    FROM fact_supply_weekly AS f
    LEFT JOIN dim_part AS p
        ON f.part_id = p.part_id
),
calc AS (
    SELECT
        *,
        GREATEST(on_hand_qty - blocked_qty, 0) AS available_inventory,
        CEIL(lead_time_days / 7.0)::integer AS lead_time_weeks,
        GREATEST(forecast_qty::numeric, avg_consumption_4w) AS demand_signal
    FROM base
),
metrics AS (
    SELECT
        *,
        ROUND(on_hand_qty * unit_cost, 2) AS on_hand_inventory_value,
        ROUND(available_inventory * unit_cost, 2) AS available_inventory_value,
        ROUND(blocked_qty * unit_cost, 2) AS blocked_inventory_value,
        ROUND(available_inventory::numeric / NULLIF(demand_signal, 0), 2) AS coverage_weeks,
        ROUND(demand_signal * lead_time_weeks, 2) AS lead_time_demand
    FROM calc
)
SELECT
    *,
    ROUND(GREATEST(lead_time_demand - available_inventory, 0), 2) AS shortage_gap_qty,
    ROUND(
        CASE
            WHEN demand_signal > 0
             AND coverage_weeks > 12
            THEN GREATEST(available_inventory - demand_signal * 12, 0)
            ELSE 0
        END,
        2
    ) AS excess_qty_candidate,
    CASE
        WHEN backorder_qty > 0
            THEN 'CONFIRMED_SHORTAGE'
        WHEN demand_signal > 0
         AND available_inventory < lead_time_demand
            THEN 'SHORTAGE_RISK'
        WHEN blocked_qty > 0
         AND blocked_qty::numeric / NULLIF(on_hand_qty, 0) >= 0.20
            THEN 'BLOCKED_STOCK'
        WHEN demand_signal > 0
         AND coverage_weeks >= 12
            THEN 'EXCESS_CANDIDATE'
        WHEN demand_signal = 0
         AND available_inventory > 0
            THEN 'NO_DEMAND_STOCK'
        ELSE 'HEALTHY'
    END AS inventory_status
FROM metrics;