-- Migration 003: Authentication and user management tables

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- User sessions for refresh tokens
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

-- API keys for programmatic access
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;

-- Project permissions
CREATE TABLE project_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    can_view BOOLEAN DEFAULT TRUE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    can_manage_users BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

CREATE INDEX idx_project_permissions_user ON project_permissions(user_id);
CREATE INDEX idx_project_permissions_project ON project_permissions(project_id);

-- Chat sessions and messages
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    title TEXT,
    context JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_project ON chat_sessions(project_id);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    is_user BOOLEAN DEFAULT TRUE,
    project_context JSONB,
    meta_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);

-- RAG documents and knowledge base
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    document_type TEXT,
    meta_data JSONB,
    embedding VECTOR(1024),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rag_documents_type ON rag_documents(document_type);
CREATE INDEX idx_rag_documents_active ON rag_documents(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_rag_documents_embedding ON rag_documents USING hnsw (embedding vector_cosine_ops);

CREATE TABLE project_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence NUMERIC(3,2) DEFAULT 1.0,
    source TEXT,
    meta_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_project_knowledge_project ON project_knowledge(project_id);
CREATE INDEX idx_project_knowledge_category ON project_knowledge(category);

-- Generated documents
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    type TEXT NOT NULL CHECK (type IN ('quote', 'planning')),
    path_pdf TEXT NOT NULL,
    snapshot_jsonb JSONB,
    version INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_generated_documents_project ON generated_documents(project_id);
CREATE INDEX idx_generated_documents_type ON generated_documents(type);

-- Add updated_at triggers for new tables
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER user_sessions_updated_at BEFORE UPDATE ON user_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER project_permissions_updated_at BEFORE UPDATE ON project_permissions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER chat_sessions_updated_at BEFORE UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER rag_documents_updated_at BEFORE UPDATE ON rag_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER project_knowledge_updated_at BEFORE UPDATE ON project_knowledge FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();