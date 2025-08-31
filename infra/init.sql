-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom ULID type if needed
CREATE OR REPLACE FUNCTION generate_ulid() RETURNS uuid AS $$
BEGIN
  RETURN uuid_generate_v7();
END;
$$ LANGUAGE plpgsql;