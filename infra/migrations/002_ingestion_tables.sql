-- Migration 002: Add ingestion pipeline tables from TDD v2
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Enhanced documents table for ingestion
ALTER TABLE documents 
ADD COLUMN filename TEXT,
ADD COLUMN mime_type TEXT,
ADD COLUMN size_bytes BIGINT,
ADD COLUMN language TEXT,
ADD COLUMN confidence NUMERIC(3,2),
ADD COLUMN storage_path TEXT,
ADD COLUMN content_sha256 TEXT UNIQUE;

-- Update existing documents to have required fields
UPDATE documents SET 
  filename = split_part(path, '/', -1),
  storage_path = path,
  content_sha256 = encode(sha256(random()::text::bytea), 'hex')
WHERE filename IS NULL;

-- Enhanced doc_chunks with FTS support
ALTER TABLE doc_chunks 
ADD COLUMN document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
ADD COLUMN tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', unaccent(coalesce(text, '')))) STORED;

CREATE INDEX doc_chunks_tsv_idx ON doc_chunks USING GIN(tsv);
CREATE INDEX doc_chunks_document_page_idx ON doc_chunks(document_id, page);

-- Extracted items table
CREATE TABLE extracted_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id),
  type TEXT NOT NULL CHECK (type IN ('line_item', 'purchase', 'shipping', 'decision', 'metadata')),
  vendor_id UUID REFERENCES vendors(id),
  material_id UUID REFERENCES materials(id),
  title TEXT,
  qty NUMERIC(14,3),
  unit TEXT,
  unit_price_nis NUMERIC(14,2),
  vat_pct NUMERIC(5,2),
  lead_time_days NUMERIC(6,2),
  attrs JSONB,
  source_ref TEXT NOT NULL,
  evidence TEXT,
  confidence NUMERIC(3,2) DEFAULT 0.8,
  occurred_at DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_extracted_items_project_type ON extracted_items(project_id, type);
CREATE INDEX idx_extracted_items_attrs ON extracted_items USING GIN(attrs jsonb_path_ops);
CREATE INDEX idx_extracted_items_low_conf ON extracted_items(confidence) WHERE confidence < 0.7;

-- Alias tables for fuzzy matching
CREATE TABLE vendor_aliases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  vendor_id UUID NOT NULL REFERENCES vendors(id),
  alias TEXT NOT NULL,
  source_ref TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vendor_aliases_vendor ON vendor_aliases(vendor_id);
CREATE INDEX idx_vendor_aliases_alias ON vendor_aliases USING GIN(alias gin_trgm_ops);

CREATE TABLE material_aliases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  material_id UUID NOT NULL REFERENCES materials(id),
  alias TEXT NOT NULL,
  source_ref TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_material_aliases_material ON material_aliases(material_id);
CREATE INDEX idx_material_aliases_alias ON material_aliases USING GIN(alias gin_trgm_ops);

-- Ingestion events audit table
CREATE TABLE ingest_events (
  id BIGSERIAL PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id),
  stage TEXT NOT NULL CHECK (stage IN ('upload', 'parse', 'classify', 'pack', 'extract', 'validate', 'link', 'stage', 'clarify', 'commit', 'error')),
  status TEXT NOT NULL CHECK (status IN ('start', 'ok', 'retry', 'fail')),
  payload_jsonb JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ingest_events_document ON ingest_events(document_id);
CREATE INDEX idx_ingest_events_stage_status ON ingest_events(stage, status);

-- Add pg_trgm indexes for fuzzy matching
CREATE INDEX idx_vendors_name_trgm ON vendors USING GIN(name gin_trgm_ops);
CREATE INDEX idx_materials_name_trgm ON materials USING GIN(name gin_trgm_ops);

-- Function for similarity search
CREATE OR REPLACE FUNCTION similarity_search(
  search_text TEXT,
  similarity_threshold NUMERIC DEFAULT 0.3
) RETURNS TABLE (
  id UUID,
  name TEXT,
  similarity NUMERIC,
  type TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT v.id, v.name, similarity(v.name, search_text), 'vendor'::TEXT
  FROM vendors v
  WHERE similarity(v.name, search_text) >= similarity_threshold
  
  UNION ALL
  
  SELECT m.id, m.name, similarity(m.name, search_text), 'material'::TEXT
  FROM materials m
  WHERE similarity(m.name, search_text) >= similarity_threshold
  
  ORDER BY similarity DESC;
END;
$$ LANGUAGE plpgsql;