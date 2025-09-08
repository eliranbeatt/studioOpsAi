#!/usr/bin/env python3
"""Apply the ingestion migration manually"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def apply_ingestion_migration():
    """Apply the ingestion migration to update documents table"""
    
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        print("🔄 Applying ingestion migration...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name IN ('filename', 'mime_type', 'size_bytes', 'storage_path', 'content_sha256')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if len(existing_columns) > 0:
            print(f"⚠️  Some columns already exist: {existing_columns}")
            print("   Skipping column additions...")
        else:
            # Add missing columns to documents table
            print("📝 Adding columns to documents table...")
            cursor.execute("""
                ALTER TABLE documents 
                ADD COLUMN filename TEXT,
                ADD COLUMN mime_type TEXT,
                ADD COLUMN size_bytes BIGINT,
                ADD COLUMN language TEXT,
                ADD COLUMN confidence NUMERIC(3,2),
                ADD COLUMN storage_path TEXT,
                ADD COLUMN content_sha256 TEXT;
            """)
            print("✅ Added columns to documents table")
        
        # Check if unique constraint exists
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'documents' AND constraint_type = 'UNIQUE' AND constraint_name LIKE '%content_sha256%'
        """)
        unique_constraints = cursor.fetchall()
        
        if not unique_constraints:
            print("📝 Adding unique constraint on content_sha256...")
            cursor.execute("ALTER TABLE documents ADD CONSTRAINT documents_content_sha256_key UNIQUE (content_sha256);")
            print("✅ Added unique constraint")
        else:
            print("⚠️  Unique constraint already exists")
        
        # Update existing documents to have required fields
        cursor.execute("SELECT COUNT(*) FROM documents WHERE filename IS NULL")
        null_filename_count = cursor.fetchone()[0]
        
        if null_filename_count > 0:
            print(f"📝 Updating {null_filename_count} existing documents...")
            cursor.execute("""
                UPDATE documents SET 
                  filename = split_part(path, '/', -1),
                  storage_path = path,
                  content_sha256 = encode(sha256(random()::text::bytea), 'hex')
                WHERE filename IS NULL;
            """)
            print("✅ Updated existing documents")
        
        # Check if ingest_events table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'ingest_events'
        """)
        ingest_events_exists = cursor.fetchone()
        
        if not ingest_events_exists:
            print("📝 Creating ingest_events table...")
            cursor.execute("""
                CREATE TABLE ingest_events (
                  id BIGSERIAL PRIMARY KEY,
                  document_id TEXT NOT NULL,
                  stage TEXT NOT NULL CHECK (stage IN ('upload', 'parse', 'classify', 'pack', 'extract', 'validate', 'link', 'stage', 'clarify', 'commit', 'error')),
                  status TEXT NOT NULL CHECK (status IN ('start', 'ok', 'retry', 'fail')),
                  payload_jsonb JSONB,
                  created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            cursor.execute("CREATE INDEX idx_ingest_events_document ON ingest_events(document_id);")
            cursor.execute("CREATE INDEX idx_ingest_events_stage_status ON ingest_events(stage, status);")
            print("✅ Created ingest_events table")
        else:
            print("⚠️  ingest_events table already exists")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Ingestion migration applied successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    apply_ingestion_migration()