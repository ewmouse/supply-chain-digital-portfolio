CREATE OR REPLACE VIEW vw_supplier_performance AS
WITH snapshot AS (
    SELECT MAX(date) AS snapshot_date
    FROM fact_supply_weekly
),
po_base AS (
    SELECT
        po.*,
        po.receipt_date - po.promised_date AS delivery_variance_days,
        CASE WHEN po.receipt_date <= po.promised_date THEN 1 ELSE 0 END AS on_time_flag,
        CASE WHEN po.received_qty >= po.ordered_qty THEN 1 ELSE 0 END AS in_full_flag,
        CASE WHEN po.receipt_date <= po.promised_date AND po.received_qty >= po.ordered_qty THEN 1 ELSE 0 END AS otif_flag
    FROM fact_purchase_order AS po
    CROSS JOIN snapshot AS s
    WHERE po.receipt_date <= s.snapshot_date
      AND po.order_date >= s.snapshot_date - INTERVAL '365 days'
),
po_agg AS (
    SELECT
        supplier_id,
        COUNT(*) AS po_count,
        ROUND(100.0 * AVG(on_time_flag), 1) AS on_time_pct,
        ROUND(100.0 * AVG(in_full_flag), 1) AS in_full_pct,
        ROUND(100.0 * AVG(otif_flag), 1) AS otif_pct,
        ROUND(
            100.0 * SUM(LEAST(received_qty, ordered_qty))::numeric
            / NULLIF(SUM(ordered_qty), 0),
            1
        ) AS fill_rate_pct,
        ROUND(
            AVG(
                CASE
                    WHEN delivery_variance_days > 0
                    THEN delivery_variance_days
                END
            ),
            1
        ) AS avg_late_days
    FROM po_base
    GROUP BY supplier_id
),
quality_agg AS (
    SELECT
        q.supplier_id,
        COUNT(*) AS quality_incident_count,
        COUNT(*) FILTER (
            WHERE q.defect_severity = 'Critical'
        ) AS critical_incident_count,
        SUM(q.scrap_qty) AS scrap_qty
    FROM fact_quality_incident AS q
    CROSS JOIN snapshot AS s
    WHERE q.incident_date <= s.snapshot_date
      AND q.incident_date >= s.snapshot_date - INTERVAL '365 days'
    GROUP BY q.supplier_id
),
part_exposure AS (
    SELECT
        supplier_id_primary AS supplier_id,
        COUNT(*) AS supplied_part_count,
        COUNT(*) FILTER (
            WHERE criticality_class = 'A'
        ) AS critical_a_part_count
    FROM dim_part
    GROUP BY supplier_id_primary
)
SELECT
    s.supplier_id,
    s.supplier_risk_class,
    COALESCE(p.po_count, 0) AS po_count,
    p.on_time_pct,
    p.in_full_pct,
    p.otif_pct,
    p.fill_rate_pct,
    p.avg_late_days,
    COALESCE(q.quality_incident_count, 0) AS quality_incident_count,
    COALESCE(q.critical_incident_count, 0) AS critical_incident_count,
    COALESCE(q.scrap_qty, 0) AS scrap_qty,
    COALESCE(e.supplied_part_count, 0) AS supplied_part_count,
    COALESCE(e.critical_a_part_count, 0) AS critical_a_part_count,
    CASE
        WHEN COALESCE(q.critical_incident_count, 0) > 0
            THEN 'QUALITY_ALERT'
        WHEN p.otif_pct < 50
            THEN 'DELIVERY_RISK'
        WHEN p.otif_pct < 70
            THEN 'WATCH'
        ELSE 'STABLE'
    END AS supplier_status
FROM dim_supplier AS s
LEFT JOIN po_agg AS p
    ON s.supplier_id = p.supplier_id
LEFT JOIN quality_agg AS q
    ON s.supplier_id = q.supplier_id
LEFT JOIN part_exposure AS e
    ON s.supplier_id = e.supplier_id;