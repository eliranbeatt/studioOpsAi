-- Migration: Standardize ID types to UUID
-- Run this migration carefully in production
-- This addresses the "Mixed ID types" integration test failure

BEGIN;

-- Step 1: Create backup tables
CREATE TABLE chat_sessions_backup AS SELECT * FROM chat_sessions;
CREATE TABLE chat_messages_backup AS SELECT * FROM chat_messages;

-- Step 2: Add new UUID columns to chat_sessions
ALTER TABLE chat_sessions ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
ALTER TABLE chat_sessions ADD COLUMN new_project_id UUID;

-- Step 3: Update project_id references where valid UUID format
UPDATE chat_sessions 
SET new_project_id = project_id::uuid 
WHERE project_id IS NOT NULL 
AND project_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- Step 4: Add new UUID columns to chat_messages  
ALTER TABLE chat_messages ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
ALTER TABLE chat_messages ADD COLUMN new_session_id UUID;

-- Step 5: Update session_id references using the mapping
UPDATE chat_messages 
SET new_session_id = cs.new_id
FROM chat_sessions cs 
WHERE chat_messages.session_id = cs.id;

-- Step 6: Verify data integrity
DO $$
DECLARE
    orphaned_messages INTEGER;
    invalid_sessions INTEGER;
BEGIN
    -- Check for orphaned messages after migration
    SELECT COUNT(*) INTO orphaned_messages
    FROM chat_messages cm
    LEFT JOIN chat_sessions cs ON cm.new_session_id = cs.new_id
    WHERE cm.new_session_id IS NOT NULL AND cs.new_id IS NULL;
    
    -- Check for invalid project references
    SELECT COUNT(*) INTO invalid_sessions
    FROM chat_sessions cs
    LEFT JOIN projects p ON cs.new_project_id = p.id
    WHERE cs.new_project_id IS NOT NULL AND p.id IS NULL;
    
    RAISE NOTICE 'Migration validation:';
    RAISE NOTICE 'Orphaned messages after migration: %', orphaned_messages;
    RAISE NOTICE 'Invalid project references: %', invalid_sessions;
    
    IF orphaned_messages > 0 OR invalid_sessions > 0 THEN
        RAISE EXCEPTION 'Migration validation failed - data integrity issues detected';
    END IF;
END $$;

-- Step 7: Drop old columns and rename new ones (UNCOMMENT AFTER VERIFICATION)
-- ALTER TABLE chat_sessions DROP COLUMN id, DROP COLUMN project_id;
-- ALTER TABLE chat_sessions RENAME COLUMN new_id TO id;
-- ALTER TABLE chat_sessions RENAME COLUMN new_project_id TO project_id;
-- ALTER TABLE chat_messages DROP COLUMN id, DROP COLUMN session_id;
-- ALTER TABLE chat_messages RENAME COLUMN new_id TO id;
-- ALTER TABLE chat_messages RENAME COLUMN new_session_id TO session_id;

-- Step 8: Recreate constraints (UNCOMMENT AFTER COLUMN RENAME)
-- ALTER TABLE chat_sessions ADD PRIMARY KEY (id);
-- ALTER TABLE chat_messages ADD PRIMARY KEY (id);
-- ALTER TABLE chat_messages ADD FOREIGN KEY (session_id) REFERENCES chat_sessions(id);
-- ALTER TABLE chat_sessions ADD FOREIGN KEY (project_id) REFERENCES projects(id);

-- Step 9: Drop backup tables (UNCOMMENT AFTER FULL VERIFICATION)
-- DROP TABLE chat_sessions_backup;
-- DROP TABLE chat_messages_backup;

COMMIT;