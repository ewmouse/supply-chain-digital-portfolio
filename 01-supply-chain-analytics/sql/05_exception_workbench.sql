CREATE OR REPLACE VIEW vw_exception_workbench AS
WITH latest AS (
    SELECT MAX(date) AS max_date
    FROM vw_inventory_health
),
current_inventory AS (
    SELECT
        v.*
    FROM vw_inventory_health AS v
    CROSS JOIN latest AS l
    WHERE v.date = l.max_date
),
joined AS (
    SELECT
        i.*,
        s.otif_pct,
        s.fill_rate_pct,
        s.avg_late_days,
        s.critical_incident_count,
        s.supplier_status
    FROM current_inventory AS i
    LEFT JOIN vw_supplier_performance AS s
        ON i.supplier_id = s.supplier_id
    WHERE i.inventory_status <> 'HEALTHY'
)
SELECT
    date,
    site_id,
    part_id,
    part_family,
    criticality_class,
    supplier_id,
    inventory_status AS exception_type,
    CASE
        WHEN inventory_status = 'CONFIRMED_SHORTAGE'
            THEN 'P1'
        WHEN inventory_status = 'SHORTAGE_RISK'
         AND criticality_class = 'A'
            THEN 'P1'
        WHEN inventory_status = 'SHORTAGE_RISK'
            THEN 'P2'
        WHEN inventory_status = 'BLOCKED_STOCK'
         AND criticality_class IN ('A', 'B')
            THEN 'P2'
        ELSE 'P3'
    END AS priority,
    available_inventory,
    demand_signal,
    coverage_weeks,
    lead_time_weeks,
    lead_time_demand,
    backorder_qty,
    shortage_gap_qty,
    blocked_inventory_value,
    on_hand_inventory_value,
    otif_pct,
    fill_rate_pct,
    avg_late_days,
    critical_incident_count,
    supplier_status,
    CASE
        WHEN inventory_status = 'CONFIRMED_SHORTAGE'
            THEN 'Review open supply; expedite PO; check cross-site transfer'
        WHEN inventory_status = 'SHORTAGE_RISK'
            THEN 'Review inbound PO vs lead-time demand; consider expedite or transfer'
        WHEN inventory_status = 'BLOCKED_STOCK'
            THEN 'Review quality disposition and blocked-stock release'
        WHEN inventory_status = 'EXCESS_CANDIDATE'
            THEN 'Review demand and inbound PO; consider reschedule or cross-site transfer'
        WHEN inventory_status = 'NO_DEMAND_STOCK'
            THEN 'Validate forecast or lifecycle; review cancellation or reschedule'
        ELSE 'Review exception'
    END AS suggested_action
FROM joined;