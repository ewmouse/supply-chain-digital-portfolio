-- =========================================================
-- 1. 检查当前数据库
-- =========================================================

SELECT
    current_database(),
    current_schema();


-- =========================================================
-- 2. 检查六张表的数据量
-- =========================================================

SELECT
    'dim_supplier' AS table_name,
    COUNT(*) AS row_count
FROM dim_supplier

UNION ALL

SELECT
    'dim_site',
    COUNT(*)
FROM dim_site

UNION ALL

SELECT
    'dim_part',
    COUNT(*)
FROM dim_part

UNION ALL

SELECT
    'fact_supply_weekly',
    COUNT(*)
FROM fact_supply_weekly

UNION ALL

SELECT
    'fact_purchase_order',
    COUNT(*)
FROM fact_purchase_order

UNION ALL

SELECT
    'fact_quality_incident',
    COUNT(*)
FROM fact_quality_incident;

SELECT
    f.date,
    f.site_id,
    f.part_id,
    p.part_family,
    p.criticality_class,
    p.unit_cost,
    p.lead_time_days,
    p.supplier_id_primary,
    f.consumption_qty,
    f.on_hand_qty,
    f.blocked_qty,
    f.backorder_qty,
    f.forecast_qty

FROM fact_supply_weekly AS f

LEFT JOIN dim_part AS p
    ON f.part_id = p.part_id

ORDER BY
    f.date DESC,
    f.site_id,
    f.part_id

LIMIT 20;