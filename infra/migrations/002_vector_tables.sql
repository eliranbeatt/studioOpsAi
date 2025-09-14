-- Vector storage for chunks/memories
CREATE TABLE IF NOT EXISTS doc_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    source TEXT,
    page INTEGER,
    text TEXT,
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding ON doc_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID,
    scope_keys JSONB,
    text TEXT,
    source_ref TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    embedding VECTOR(1024)
);

CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING hnsw (embedding vector_cosine_ops);
