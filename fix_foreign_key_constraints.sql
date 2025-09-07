-- Migration: Fix Foreign Key Constraints for Project Deletion
-- This script fixes foreign key constraints to allow proper project deletion
-- without violating referential integrity

BEGIN;

-- Fix chat_sessions foreign key constraint
-- Change from NO ACTION to SET NULL so chat sessions can exist without projects
ALTER TABLE chat_sessions 
DROP CONSTRAINT IF EXISTS chat_sessions_project_id_fkey;

ALTER TABLE chat_sessions 
ADD CONSTRAINT chat_sessions_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- Fix documents foreign key constraint  
-- Change from NO ACTION to SET NULL so documents can exist without projects
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS documents_project_id_fkey;

ALTER TABLE documents 
ADD CONSTRAINT documents_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- Fix purchases foreign key constraint
-- Change from NO ACTION to SET NULL so purchase history is preserved
ALTER TABLE purchases 
DROP CONSTRAINT IF EXISTS purchases_project_id_fkey;

ALTER TABLE purchases 
ADD CONSTRAINT purchases_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- Plans already have CASCADE which is correct - they should be deleted with projects

-- Verify the changes
SELECT 
    tc.table_name, 
    kcu.column_name, 
    tc.constraint_name,
    rc.delete_rule,
    rc.update_rule
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
    LEFT JOIN information_schema.referential_constraints AS rc
      ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND ccu.table_name = 'projects'
ORDER BY tc.table_name, kcu.column_name;

COMMIT;