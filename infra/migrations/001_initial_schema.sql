-- Initial database schema for StudioOps AI
-- Migration 001: Create all core tables

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vendors & Materials
CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    contact JSONB,
    url TEXT,
    rating SMALLINT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    spec TEXT,
    unit TEXT NOT NULL,
    category TEXT,
    typical_waste_pct NUMERIC(5,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendor_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID REFERENCES vendors(id),
    material_id UUID REFERENCES materials(id),
    sku TEXT,
    price_nis NUMERIC(14,2) NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    source_url TEXT,
    confidence NUMERIC(3,2) DEFAULT 0.8,
    is_quote BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(vendor_id, material_id, sku, fetched_at)
);

CREATE INDEX IF NOT EXISTS idx_vendor_prices_material_fetched ON vendor_prices(material_id, fetched_at DESC);

-- Projects & Plans
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    client_name TEXT,
    board_id TEXT,
    status TEXT,
    start_date DATE,
    due_date DATE,
    budget_planned NUMERIC(14,2),
    budget_actual NUMERIC(14,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    status TEXT CHECK (status IN ('draft','approved','archived')),
    margin_target NUMERIC(4,3) DEFAULT 0.25,
    currency TEXT DEFAULT 'NIS',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, version)
);

CREATE TABLE IF NOT EXISTS plan_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES plans(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    quantity NUMERIC(14,3) DEFAULT 1,
    unit TEXT,
    unit_price NUMERIC(14,2),
    unit_price_source JSONB,
    vendor_id UUID REFERENCES vendors(id),
    labor_role TEXT,
    labor_hours NUMERIC(10,2),
    lead_time_days NUMERIC(6,2),
    dependency_ids JSONB,
    risk_level TEXT,
    notes TEXT,
    subtotal NUMERIC(14,2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plan_items_plan_id ON plan_items(plan_id);

-- Shipping & Labor models
CREATE TABLE IF NOT EXISTS shipping_quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_hash TEXT,
    distance_km NUMERIC(10,2),
    weight_kg NUMERIC(10,2),
    type TEXT,
    base_fee_nis NUMERIC(14,2),
    per_km_nis NUMERIC(10,2),
    per_kg_nis NUMERIC(10,2),
    surge_json JSONB,
    fetched_at TIMESTAMPTZ,
    source TEXT,
    confidence NUMERIC(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rate_cards (
    role TEXT PRIMARY KEY,
    hourly_rate_nis NUMERIC(10,2) NOT NULL,
    overtime_rules_json JSONB,
    default_efficiency NUMERIC(3,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Expenses & Purchases
CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID REFERENCES vendors(id),
    material_id UUID REFERENCES materials(id),
    project_id UUID REFERENCES projects(id),
    qty NUMERIC(14,3),
    unit_price_nis NUMERIC(14,2),
    tax_vat_pct NUMERIC(5,2),
    occurred_at DATE,
    receipt_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    type TEXT,
    path TEXT NOT NULL,
    snapshot_jsonb JSONB,
    version INTEGER,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);



-- Outbox for CDC
CREATE TABLE IF NOT EXISTS outbox (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    delivered BOOLEAN DEFAULT FALSE
);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS vendors_updated_at ON vendors;
DROP TRIGGER IF EXISTS vendors_updated_at ON vendors;
DROP TRIGGER IF EXISTS vendors_updated_at ON vendors;
DROP TRIGGER IF EXISTS vendors_updated_at ON vendors;
DROP TRIGGER IF EXISTS vendors_updated_at ON vendors;
DROP TRIGGER IF EXISTS vendors_updated_at ON vendors;
CREATE TRIGGER vendors_updated_at BEFORE UPDATE ON vendors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
DROP TRIGGER IF EXISTS materials_updated_at ON materials;
CREATE TRIGGER materials_updated_at BEFORE UPDATE ON materials FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS projects_updated_at ON projects;
CREATE TRIGGER projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
DROP TRIGGER IF EXISTS plans_updated_at ON plans;
CREATE TRIGGER plans_updated_at BEFORE UPDATE ON plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS rate_cards_updated_at ON rate_cards;
CREATE TRIGGER rate_cards_updated_at BEFORE UPDATE ON rate_cards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();olumn();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();n();