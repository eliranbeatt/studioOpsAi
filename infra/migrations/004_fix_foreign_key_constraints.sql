-- Migration 004: Fix Foreign Key Constraints for Safe Project Deletion
-- This migration fixes foreign key constraints to allow safe project deletion
-- by setting proper ON DELETE actions for all project relationships

-- Enable required extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- First, let's add the missing chat_sessions table if it doesn't exist
-- (based on the models.py, this table should exist but might not be in migrations)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT,
    project_id UUID,
    title TEXT,
    context JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add missing chat_messages table if it doesn't exist
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    is_user BOOLEAN DEFAULT TRUE,
    project_context JSONB,
    meta_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Function to safely drop and recreate foreign key constraints
CREATE OR REPLACE FUNCTION fix_foreign_key_constraints()
RETURNS void AS $$
DECLARE
    constraint_record RECORD;
BEGIN
    -- Log the start of the migration
    RAISE NOTICE 'Starting foreign key constraint fixes...';
    
    -- 1. Fix chat_sessions foreign key constraint
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'chat_sessions_project_id_fkey' 
        AND table_name = 'chat_sessions'
    ) THEN
        ALTER TABLE chat_sessions DROP CONSTRAINT chat_sessions_project_id_fkey;
        RAISE NOTICE 'Dropped existing chat_sessions foreign key constraint';
    END IF;
    
    -- Add new constraint with ON DELETE SET NULL
    ALTER TABLE chat_sessions 
    ADD CONSTRAINT chat_sessions_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(id) 
    ON DELETE SET NULL;
    
    RAISE NOTICE 'Added chat_sessions foreign key with ON DELETE SET NULL';
    
    -- 2. Fix documents foreign key constraint
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'documents_project_id_fkey' 
        AND table_name = 'documents'
    ) THEN
        ALTER TABLE documents DROP CONSTRAINT documents_project_id_fkey;
        RAISE NOTICE 'Dropped existing documents foreign key constraint';
    END IF;
    
    -- Add new constraint with ON DELETE SET NULL
    ALTER TABLE documents 
    ADD CONSTRAINT documents_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(id) 
    ON DELETE SET NULL;
    
    RAISE NOTICE 'Added documents foreign key with ON DELETE SET NULL';
    
    -- 3. Fix purchases foreign key constraint
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'purchases_project_id_fkey' 
        AND table_name = 'purchases'
    ) THEN
        ALTER TABLE purchases DROP CONSTRAINT purchases_project_id_fkey;
        RAISE NOTICE 'Dropped existing purchases foreign key constraint';
    END IF;
    
    -- Add new constraint with ON DELETE SET NULL
    ALTER TABLE purchases 
    ADD CONSTRAINT purchases_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(id) 
    ON DELETE SET NULL;
    
    RAISE NOTICE 'Added purchases foreign key with ON DELETE SET NULL';
    
    -- 4. Fix extracted_items foreign key constraint (if table exists)
    -- Note: extracted_items.project_id is VARCHAR, projects.id is UUID - incompatible types
    -- We'll skip this constraint for now and handle it separately if needed
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'extracted_items') THEN
        -- Check if project_id column is UUID type
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'extracted_items' 
            AND column_name = 'project_id' 
            AND data_type = 'uuid'
        ) THEN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'extracted_items_project_id_fkey' 
                AND table_name = 'extracted_items'
            ) THEN
                ALTER TABLE extracted_items DROP CONSTRAINT extracted_items_project_id_fkey;
                RAISE NOTICE 'Dropped existing extracted_items foreign key constraint';
            END IF;
            
            ALTER TABLE extracted_items 
            ADD CONSTRAINT extracted_items_project_id_fkey 
            FOREIGN KEY (project_id) REFERENCES projects(id) 
            ON DELETE SET NULL;
            
            RAISE NOTICE 'Added extracted_items foreign key with ON DELETE SET NULL';
        ELSE
            RAISE NOTICE 'Skipping extracted_items foreign key - data type mismatch (VARCHAR vs UUID)';
        END IF;
    END IF;
    
    -- 5. Fix doc_chunks foreign key constraint (if it references projects)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'doc_chunks') THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'doc_chunks_project_id_fkey' 
            AND table_name = 'doc_chunks'
        ) THEN
            ALTER TABLE doc_chunks DROP CONSTRAINT doc_chunks_project_id_fkey;
            RAISE NOTICE 'Dropped existing doc_chunks foreign key constraint';
        END IF;
        
        -- Only add if project_id column exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'doc_chunks' AND column_name = 'project_id'
        ) THEN
            ALTER TABLE doc_chunks 
            ADD CONSTRAINT doc_chunks_project_id_fkey 
            FOREIGN KEY (project_id) REFERENCES projects(id) 
            ON DELETE SET NULL;
            
            RAISE NOTICE 'Added doc_chunks foreign key with ON DELETE SET NULL';
        END IF;
    END IF;
    
    -- 6. Verify that plans foreign key has CASCADE (this should already be correct)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'plans') THEN
        -- Check if the constraint exists and has the right action
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.referential_constraints rc
            JOIN information_schema.table_constraints tc ON rc.constraint_name = tc.constraint_name
            WHERE tc.table_name = 'plans' 
            AND tc.constraint_name = 'plans_project_id_fkey'
            AND rc.delete_rule = 'CASCADE'
        ) THEN
            -- Drop and recreate with CASCADE
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'plans_project_id_fkey' 
                AND table_name = 'plans'
            ) THEN
                ALTER TABLE plans DROP CONSTRAINT plans_project_id_fkey;
            END IF;
            
            ALTER TABLE plans 
            ADD CONSTRAINT plans_project_id_fkey 
            FOREIGN KEY (project_id) REFERENCES projects(id) 
            ON DELETE CASCADE;
            
            RAISE NOTICE 'Fixed plans foreign key with ON DELETE CASCADE';
        ELSE
            RAISE NOTICE 'Plans foreign key already has correct CASCADE action';
        END IF;
    END IF;
    
    RAISE NOTICE 'Foreign key constraint fixes completed successfully!';
    
END;
$$ LANGUAGE plpgsql;

-- Execute the function to fix constraints
SELECT fix_foreign_key_constraints();

-- Drop the function after use
DROP FUNCTION fix_foreign_key_constraints();

-- Add indexes for better performance on foreign key columns
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project_id ON chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_purchases_project_id ON purchases(project_id);

-- Add updated_at trigger for chat_sessions if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'chat_sessions_updated_at'
    ) THEN
        CREATE TRIGGER chat_sessions_updated_at 
        BEFORE UPDATE ON chat_sessions 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Verify the constraints are properly set
DO $$
DECLARE
    constraint_info RECORD;
BEGIN
    RAISE NOTICE 'Verifying foreign key constraints:';
    
    FOR constraint_info IN
        SELECT 
            tc.table_name,
            tc.constraint_name,
            rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.referential_constraints rc 
            ON tc.constraint_name = rc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name IN ('chat_sessions', 'documents', 'purchases', 'plans', 'extracted_items', 'doc_chunks')
        AND rc.unique_constraint_name IN (
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'projects' AND constraint_type = 'PRIMARY KEY'
        )
        ORDER BY tc.table_name
    LOOP
        RAISE NOTICE '  %: % (ON DELETE %)', 
            constraint_info.table_name, 
            constraint_info.constraint_name, 
            constraint_info.delete_rule;
    END LOOP;
END $$;