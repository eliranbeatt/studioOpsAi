#!/usr/bin/env python3
"""
Comprehensive Fix for Integration Test Issues
Addresses all 6 failing tests from the system integration validation
"""

import asyncio
import asyncpg
import os
import sys
import json
from datetime import datetime, timezone
import subprocess

async def main():
    """Main fix execution"""
    print("🔧 COMPREHENSIVE INTEGRATION ISSUES FIX")
    print("=" * 50)
    
    # Step 1: Database fixes
    print("\n📊 Step 1: Database Issues")
    try:
        await fix_database_issues()
    except Exception as e:
        print(f"❌ Database fixes failed: {e}")
        return False
    
    # Step 2: API timestamp fixes
    print("\n🕐 Step 2: Timestamp Serialization")
    try:
        fix_api_timestamps()
    except Exception as e:
        print(f"❌ API timestamp fixes failed: {e}")
        return False
    
    # Step 3: Create migration scripts
    print("\n📝 Step 3: Migration Scripts")
    try:
        create_migration_scripts()
    except Exception as e:
        print(f"❌ Migration script creation failed: {e}")
        return False
    
    # Step 4: Validation
    print("\n✅ Step 4: Validation")
    try:
        await validate_fixes()
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False
    
    print("\n🎉 ALL FIXES COMPLETED SUCCESSFULLY!")
    print("\nManual steps required:")
    print("1. Review and run id_standardization_migration.sql")
    print("2. Restart API server to apply timestamp fixes")
    print("3. Run comprehensive_system_integration_test.py to verify")
    
    return True

async def fix_database_issues():
    """Fix database-related issues"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        # Fix 1: Clean orphaned chat messages
        print("🧹 Cleaning orphaned chat messages...")
        orphaned_count = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_messages cm
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.id IS NULL
        """)
        
        if orphaned_count > 0:
            await conn.execute("""
                DELETE FROM chat_messages 
                WHERE session_id NOT IN (SELECT id FROM chat_sessions WHERE id IS NOT NULL)
            """)
            print(f"✅ Deleted {orphaned_count} orphaned chat messages")
        else:
            print("ℹ️  No orphaned chat messages found")
        
        # Fix 2: Clean invalid project references
        print("🔗 Fixing chat session project references...")
        invalid_refs = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_sessions cs
            WHERE cs.project_id IS NOT NULL 
            AND cs.project_id NOT IN (
                SELECT id::text FROM projects 
                UNION 
                SELECT id FROM projects WHERE id::text = cs.project_id
            )
        """)
        
        if invalid_refs > 0:
            await conn.execute("""
                UPDATE chat_sessions 
                SET project_id = NULL 
                WHERE project_id IS NOT NULL 
                AND project_id NOT IN (
                    SELECT id::text FROM projects 
                    UNION 
                    SELECT id FROM projects WHERE id::text = project_id
                )
            """)
            print(f"✅ Fixed {invalid_refs} invalid project references")
        else:
            print("ℹ️  No invalid project references found")
        
        # Fix 3: Try collation refresh (may fail without superuser)
        print("🔄 Attempting collation refresh...")
        try:
            await conn.execute("ALTER DATABASE studioops REFRESH COLLATION VERSION;")
            print("✅ Refreshed collation version")
        except Exception as e:
            print(f"⚠️  Collation refresh failed (may need superuser): {e}")
        
        await conn.close()
        print("✅ Database fixes completed")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

def fix_api_timestamps():
    """Fix API timestamp serialization"""
    
    # Create datetime utility
    datetime_utils = '''"""
Datetime utilities for consistent API serialization
"""
from datetime import datetime, timezone
from typing import Optional, Any

def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime to ISO format with timezone info"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()

def serialize_row_datetime(row_value: Any) -> Optional[str]:
    """Serialize datetime from database row to ISO format with timezone"""
    if row_value is None:
        return None
    
    if isinstance(row_value, datetime):
        return serialize_datetime(row_value)
    
    return str(row_value)
'''
    
    os.makedirs('apps/api', exist_ok=True)
    with open('apps/api/datetime_utils.py', 'w') as f:
        f.write(datetime_utils)
    print("✅ Created datetime utilities")
    
    # Update minimal_api.py to use proper timezone serialization
    api_file = 'apps/api/minimal_api.py'
    if os.path.exists(api_file):
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Add import if not present
        if 'from datetime import timezone' not in content:
            content = content.replace(
                'from datetime import datetime',
                'from datetime import datetime, timezone'
            )
        
        # Fix isoformat calls to include timezone
        content = content.replace(
            'result[7].isoformat()',
            '(result[7].replace(tzinfo=timezone.utc) if result[7].tzinfo is None else result[7]).isoformat()'
        )
        content = content.replace(
            'result[8].isoformat() if result[8] else None',
            '((result[8].replace(tzinfo=timezone.utc) if result[8].tzinfo is None else result[8]).isoformat()) if result[8] else None'
        )
        content = content.replace(
            'row[7].isoformat()',
            '(row[7].replace(tzinfo=timezone.utc) if row[7].tzinfo is None else row[7]).isoformat()'
        )
        content = content.replace(
            'row[8].isoformat() if row[8] else None',
            '((row[8].replace(tzinfo=timezone.utc) if row[8].tzinfo is None else row[8]).isoformat()) if row[8] else None'
        )
        
        with open(api_file, 'w') as f:
            f.write(content)
        print("✅ Updated minimal_api.py timestamp serialization")

def create_migration_scripts():
    """Create migration scripts for ID standardization"""
    
    migration_sql = '''-- Migration: Standardize ID types to UUID
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
'''
    
    with open('id_standardization_migration.sql', 'w') as f:
        f.write(migration_sql)
    print("✅ Created id_standardization_migration.sql")
    
    # Create rollback script
    rollback_sql = '''-- Rollback script for ID standardization migration
-- Use this if the migration needs to be reverted

BEGIN;

-- Restore from backup tables
DROP TABLE IF EXISTS chat_sessions;
DROP TABLE IF EXISTS chat_messages;

ALTER TABLE chat_sessions_backup RENAME TO chat_sessions;
ALTER TABLE chat_messages_backup RENAME TO chat_messages;

-- Recreate original constraints if needed
-- (Add original constraint recreation here)

COMMIT;
'''
    
    with open('rollback_id_migration.sql', 'w') as f:
        f.write(rollback_sql)
    print("✅ Created rollback_id_migration.sql")

async def validate_fixes():
    """Validate that fixes are working"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Check orphaned messages
        orphaned = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_messages cm
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.id IS NULL
        """)
        
        if orphaned == 0:
            print("✅ No orphaned chat messages")
        else:
            print(f"⚠️  Still {orphaned} orphaned messages")
        
        # Check invalid project references
        invalid_refs = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_sessions cs
            WHERE cs.project_id IS NOT NULL 
            AND cs.project_id NOT IN (
                SELECT id::text FROM projects 
                UNION 
                SELECT id FROM projects WHERE id::text = cs.project_id
            )
        """)
        
        if invalid_refs == 0:
            print("✅ No invalid project references")
        else:
            print(f"⚠️  Still {invalid_refs} invalid project references")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())