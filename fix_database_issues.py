#!/usr/bin/env python3
"""
Fix Database Issues Script
Addresses the 6 failing integration tests
"""

import asyncio
import asyncpg
import os
from datetime import datetime
import json

async def fix_database_issues():
    """Fix all database-related issues from integration tests"""
    
    # Database connection
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/studioops')
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Fix 1: PostgreSQL Collation Version
        print("\n=== Fix 1: PostgreSQL Collation Version ===")
        try:
            await conn.execute("ALTER DATABASE studioops REFRESH COLLATION VERSION;")
            print("✅ Refreshed collation version")
        except Exception as e:
            print(f"⚠️  Collation refresh failed (may need superuser): {e}")
        
        # Fix 2: Standardize ID Types - Convert chat tables to UUID
        print("\n=== Fix 2: Standardize ID Types ===")
        
        # Check current chat_sessions structure
        sessions_result = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_sessions' AND column_name IN ('id', 'project_id')
        """)
        print(f"Current chat_sessions ID types: {dict(sessions_result)}")
        
        # Check current chat_messages structure  
        messages_result = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' AND column_name IN ('id', 'session_id')
        """)
        print(f"Current chat_messages ID types: {dict(messages_result)}")
        
        # Fix 3: Clean up orphaned chat messages
        print("\n=== Fix 3: Clean Orphaned Chat Messages ===")
        
        # Find orphaned messages
        orphaned_count = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_messages cm
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.id IS NULL
        """)
        print(f"Found {orphaned_count} orphaned chat messages")
        
        if orphaned_count > 0:
            # Delete orphaned messages
            deleted = await conn.execute("""
                DELETE FROM chat_messages 
                WHERE session_id NOT IN (SELECT id FROM chat_sessions WHERE id IS NOT NULL)
            """)
            print(f"✅ Deleted orphaned chat messages: {deleted}")
        
        # Fix 4: Fix chat session project references
        print("\n=== Fix 4: Fix Chat Session Project References ===")
        
        # Check for invalid project references in chat_sessions
        invalid_refs = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_sessions cs
            LEFT JOIN projects p ON cs.project_id::uuid = p.id
            WHERE cs.project_id IS NOT NULL AND p.id IS NULL
        """)
        print(f"Found {invalid_refs} chat sessions with invalid project references")
        
        if invalid_refs > 0:
            # Clean up invalid project references
            await conn.execute("""
                UPDATE chat_sessions 
                SET project_id = NULL 
                WHERE project_id IS NOT NULL 
                AND project_id::uuid NOT IN (SELECT id FROM projects)
            """)
            print("✅ Cleaned up invalid project references")
        
        # Fix 5: Create migration for ID type standardization
        print("\n=== Fix 5: Create ID Standardization Migration ===")
        
        migration_sql = """
-- Migration to standardize ID types to UUID
-- This should be run carefully in production

BEGIN;

-- Step 1: Add new UUID columns to chat_sessions
ALTER TABLE chat_sessions ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
ALTER TABLE chat_sessions ADD COLUMN new_project_id UUID;

-- Step 2: Update project_id references where valid
UPDATE chat_sessions 
SET new_project_id = project_id::uuid 
WHERE project_id IS NOT NULL 
AND project_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- Step 3: Add new UUID columns to chat_messages  
ALTER TABLE chat_messages ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
ALTER TABLE chat_messages ADD COLUMN new_session_id UUID;

-- Step 4: Update session_id references using the mapping
UPDATE chat_messages 
SET new_session_id = cs.new_id
FROM chat_sessions cs 
WHERE chat_messages.session_id = cs.id;

-- Step 5: Drop old columns and rename new ones
-- (This would be done in a separate migration after verification)
-- ALTER TABLE chat_sessions DROP COLUMN id, DROP COLUMN project_id;
-- ALTER TABLE chat_sessions RENAME COLUMN new_id TO id;
-- ALTER TABLE chat_sessions RENAME COLUMN new_project_id TO project_id;
-- ALTER TABLE chat_messages DROP COLUMN id, DROP COLUMN session_id;
-- ALTER TABLE chat_messages RENAME COLUMN new_id TO id;
-- ALTER TABLE chat_messages RENAME COLUMN new_session_id TO session_id;

COMMIT;
"""
        
        # Save migration for manual review
        with open('id_standardization_migration.sql', 'w') as f:
            f.write(migration_sql)
        print("✅ Created id_standardization_migration.sql for review")
        
        # Fix 6: Add proper foreign key constraints after ID standardization
        print("\n=== Fix 6: Verify Foreign Key Constraints ===")
        
        # Check existing constraints
        constraints = await conn.fetch("""
            SELECT conname, contype, pg_get_constraintdef(oid) as definition
            FROM pg_constraint 
            WHERE conrelid IN (
                SELECT oid FROM pg_class WHERE relname IN ('chat_sessions', 'chat_messages')
            )
        """)
        
        print("Current constraints:")
        for constraint in constraints:
            print(f"  {constraint['conname']}: {constraint['definition']}")
        
        print("\n=== Summary ===")
        print("✅ Cleaned orphaned chat messages")
        print("✅ Fixed invalid project references")
        print("✅ Created migration script for ID standardization")
        print("⚠️  Manual steps required:")
        print("   1. Review and run id_standardization_migration.sql")
        print("   2. Update API serialization to handle timezone formats")
        print("   3. Test chat-project linking after ID migration")
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_database_issues())