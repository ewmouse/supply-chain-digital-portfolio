CREATE TABLE IF NOT EXISTS dim_supplier (
    supplier_id VARCHAR(10) PRIMARY KEY,
    supplier_risk_class VARCHAR(10) NOT NULL
);


CREATE TABLE IF NOT EXISTS dim_site (
    site_id VARCHAR(10) PRIMARY KEY
);


CREATE TABLE IF NOT EXISTS dim_part (
    part_id VARCHAR(10) PRIMARY KEY,
    part_family VARCHAR(50) NOT NULL,
    criticality_class VARCHAR(5) NOT NULL,
    unit_cost NUMERIC(12, 2) NOT NULL,
    lead_time_days INTEGER NOT NULL,
    supplier_id_primary VARCHAR(10) NOT NULL,
    is_repairable BOOLEAN NOT NULL,
    shelf_life_days INTEGER,

    CONSTRAINT fk_part_supplier
        FOREIGN KEY (supplier_id_primary)
        REFERENCES dim_supplier(supplier_id)
);


CREATE TABLE IF NOT EXISTS fact_supply_weekly (
    date DATE NOT NULL,
    site_id VARCHAR(10) NOT NULL,
    part_id VARCHAR(10) NOT NULL,

    planned_maintenance BOOLEAN NOT NULL,
    consumption_qty INTEGER NOT NULL,
    on_hand_qty INTEGER NOT NULL,
    backorder_qty INTEGER NOT NULL,
    blocked_qty INTEGER NOT NULL,
    forecast_qty INTEGER NOT NULL,
    forecast_type VARCHAR(20) NOT NULL,
    forecast_uplift_pct NUMERIC(10, 4) NOT NULL,

    PRIMARY KEY (date, site_id, part_id),

    CONSTRAINT fk_supply_site
        FOREIGN KEY (site_id)
        REFERENCES dim_site(site_id),

    CONSTRAINT fk_supply_part
        FOREIGN KEY (part_id)
        REFERENCES dim_part(part_id)
);


CREATE TABLE IF NOT EXISTS fact_purchase_order (
    po_id VARCHAR(20) PRIMARY KEY,

    supplier_id VARCHAR(10) NOT NULL,
    site_id VARCHAR(10) NOT NULL,
    part_id VARCHAR(10) NOT NULL,

    order_date DATE NOT NULL,
    promised_date DATE NOT NULL,
    receipt_date DATE NOT NULL,

    ordered_qty INTEGER NOT NULL,
    received_qty INTEGER NOT NULL,

    CONSTRAINT fk_po_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES dim_supplier(supplier_id),

    CONSTRAINT fk_po_site
        FOREIGN KEY (site_id)
        REFERENCES dim_site(site_id),

    CONSTRAINT fk_po_part
        FOREIGN KEY (part_id)
        REFERENCES dim_part(part_id)
);


CREATE TABLE IF NOT EXISTS fact_quality_incident (
    incident_id VARCHAR(20) PRIMARY KEY,

    incident_date DATE NOT NULL,
    part_id VARCHAR(10) NOT NULL,
    supplier_id VARCHAR(10) NOT NULL,
    site_id VARCHAR(10) NOT NULL,

    defect_severity VARCHAR(20) NOT NULL,
    defect_type VARCHAR(50) NOT NULL,
    scrap_qty INTEGER NOT NULL,

    CONSTRAINT fk_quality_part
        FOREIGN KEY (part_id)
        REFERENCES dim_part(part_id),

    CONSTRAINT fk_quality_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES dim_supplier(supplier_id),

    CONSTRAINT fk_quality_site
        FOREIGN KEY (site_id)
        REFERENCES dim_site(site_id)
);