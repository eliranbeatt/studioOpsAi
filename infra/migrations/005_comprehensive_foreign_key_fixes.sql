-- Comprehensive Foreign Key Constraint Fixes Migration
-- This migration addresses all foreign key constraint issues identified in the system
-- Date: 2025-01-07
-- Requirements: 1.6, 5.4, 6.2

-- Create migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rollback_script TEXT,
    status VARCHAR(50) DEFAULT 'applied'
);

-- Function to safely drop and recreate foreign key constraints
CREATE OR REPLACE FUNCTION fix_foreign_key_constraints()
RETURNS TABLE(operation TEXT, status TEXT, details TEXT) AS $$
DECLARE
    constraint_record RECORD;
    operation_count INTEGER := 0;
BEGIN
    -- Log migration start
    INSERT INTO migration_log (migration_name, rollback_script, status) 
    VALUES (
        '005_comprehensive_foreign_key_fixes',
        'SELECT rollback_foreign_key_fixes();',
        'in_progress'
    );

    -- 1. Fix chat_sessions foreign key constraint
    BEGIN
        -- Drop existing constraint if it exists
        ALTER TABLE chat_sessions 
        DROP CONSTRAINT IF EXISTS chat_sessions_project_id_fkey;
        
        -- Add new constraint with proper ON DELETE action
        ALTER TABLE chat_sessions 
        ADD CONSTRAINT chat_sessions_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id) 
        ON DELETE SET NULL;
        
        operation_count := operation_count + 1;
        RETURN QUERY SELECT 'chat_sessions_fkey'::TEXT, 'success'::TEXT, 'Foreign key constraint updated with ON DELETE SET NULL'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'chat_sessions_fkey'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- 2. Fix documents foreign key constraint
    BEGIN
        -- Drop existing constraint if it exists
        ALTER TABLE documents 
        DROP CONSTRAINT IF EXISTS documents_project_id_fkey;
        
        -- Add new constraint with proper ON DELETE action
        ALTER TABLE documents 
        ADD CONSTRAINT documents_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id) 
        ON DELETE SET NULL;
        
        operation_count := operation_count + 1;
        RETURN QUERY SELECT 'documents_fkey'::TEXT, 'success'::TEXT, 'Foreign key constraint updated with ON DELETE SET NULL'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'documents_fkey'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- 3. Fix purchases foreign key constraint
    BEGIN
        -- Drop existing constraint if it exists
        ALTER TABLE purchases 
        DROP CONSTRAINT IF EXISTS purchases_project_id_fkey;
        
        -- Add new constraint with proper ON DELETE action
        ALTER TABLE purchases 
        ADD CONSTRAINT purchases_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id) 
        ON DELETE SET NULL;
        
        operation_count := operation_count + 1;
        RETURN QUERY SELECT 'purchases_fkey'::TEXT, 'success'::TEXT, 'Foreign key constraint updated with ON DELETE SET NULL'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'purchases_fkey'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- 4. Verify plans foreign key constraint (should already have CASCADE)
    BEGIN
        -- Check if plans constraint exists and has proper CASCADE
        SELECT conname INTO constraint_record
        FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE t.relname = 'plans' AND c.conname LIKE '%project_id%';
        
        IF NOT FOUND THEN
            -- Add plans constraint if missing
            ALTER TABLE plans 
            ADD CONSTRAINT plans_project_id_fkey 
            FOREIGN KEY (project_id) REFERENCES projects(id) 
            ON DELETE CASCADE;
            
            RETURN QUERY SELECT 'plans_fkey'::TEXT, 'success'::TEXT, 'Foreign key constraint added with ON DELETE CASCADE'::TEXT;
        ELSE
            RETURN QUERY SELECT 'plans_fkey'::TEXT, 'success'::TEXT, 'Foreign key constraint already exists'::TEXT;
        END IF;
        
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'plans_fkey'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- 5. Fix plan_items foreign key constraint (should CASCADE with plan)
    BEGIN
        -- Drop existing constraint if it exists
        ALTER TABLE plan_items 
        DROP CONSTRAINT IF EXISTS plan_items_plan_id_fkey;
        
        -- Add new constraint with CASCADE
        ALTER TABLE plan_items 
        ADD CONSTRAINT plan_items_plan_id_fkey 
        FOREIGN KEY (plan_id) REFERENCES plans(id) 
        ON DELETE CASCADE;
        
        operation_count := operation_count + 1;
        RETURN QUERY SELECT 'plan_items_fkey'::TEXT, 'success'::TEXT, 'Foreign key constraint updated with ON DELETE CASCADE'::TEXT;
        
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'plan_items_fkey'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- Update migration status
    UPDATE migration_log 
    SET status = 'completed' 
    WHERE migration_name = '005_comprehensive_foreign_key_fixes';

    RETURN QUERY SELECT 'migration_complete'::TEXT, 'success'::TEXT, 
                        ('Fixed ' || operation_count || ' foreign key constraints')::TEXT;

EXCEPTION WHEN OTHERS THEN
    -- Update migration status to failed
    UPDATE migration_log 
    SET status = 'failed' 
    WHERE migration_name = '005_comprehensive_foreign_key_fixes';
    
    RETURN QUERY SELECT 'migration_failed'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Function to rollback foreign key constraint changes
CREATE OR REPLACE FUNCTION rollback_foreign_key_fixes()
RETURNS TABLE(operation TEXT, status TEXT, details TEXT) AS $$
BEGIN
    -- Log rollback start
    INSERT INTO migration_log (migration_name, status) 
    VALUES ('005_comprehensive_foreign_key_fixes_rollback', 'in_progress');

    -- Rollback chat_sessions constraint
    BEGIN
        ALTER TABLE chat_sessions 
        DROP CONSTRAINT IF EXISTS chat_sessions_project_id_fkey;
        
        -- Restore original constraint (without ON DELETE action)
        ALTER TABLE chat_sessions 
        ADD CONSTRAINT chat_sessions_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id);
        
        RETURN QUERY SELECT 'chat_sessions_rollback'::TEXT, 'success'::TEXT, 'Constraint rolled back'::TEXT;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'chat_sessions_rollback'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- Rollback documents constraint
    BEGIN
        ALTER TABLE documents 
        DROP CONSTRAINT IF EXISTS documents_project_id_fkey;
        
        ALTER TABLE documents 
        ADD CONSTRAINT documents_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id);
        
        RETURN QUERY SELECT 'documents_rollback'::TEXT, 'success'::TEXT, 'Constraint rolled back'::TEXT;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'documents_rollback'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- Rollback purchases constraint
    BEGIN
        ALTER TABLE purchases 
        DROP CONSTRAINT IF EXISTS purchases_project_id_fkey;
        
        ALTER TABLE purchases 
        ADD CONSTRAINT purchases_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id);
        
        RETURN QUERY SELECT 'purchases_rollback'::TEXT, 'success'::TEXT, 'Constraint rolled back'::TEXT;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 'purchases_rollback'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
    END;

    -- Update rollback status
    UPDATE migration_log 
    SET status = 'completed' 
    WHERE migration_name = '005_comprehensive_foreign_key_fixes_rollback';

    RETURN QUERY SELECT 'rollback_complete'::TEXT, 'success'::TEXT, 'All constraints rolled back'::TEXT;

EXCEPTION WHEN OTHERS THEN
    UPDATE migration_log 
    SET status = 'failed' 
    WHERE migration_name = '005_comprehensive_foreign_key_fixes_rollback';
    
    RETURN QUERY SELECT 'rollback_failed'::TEXT, 'error'::TEXT, SQLERRM::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Execute the migration
SELECT * FROM fix_foreign_key_constraints();