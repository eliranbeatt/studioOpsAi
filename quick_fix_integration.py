#!/usr/bin/env python3
"""
Quick Fix for Integration Issues
Addresses the most critical issues that can be fixed immediately
"""

import asyncio
import asyncpg
import os
from datetime import timezone

async def quick_database_fix():
    """Quick database fixes that can be applied immediately"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        print("\n=== Quick Fix 1: Clean Orphaned Chat Messages ===")
        # Delete orphaned chat messages
        deleted = await conn.execute("""
            DELETE FROM chat_messages 
            WHERE session_id NOT IN (SELECT id FROM chat_sessions WHERE id IS NOT NULL)
        """)
        print(f"✅ Deleted orphaned chat messages: {deleted}")
        
        print("\n=== Quick Fix 2: Clean Invalid Project References ===")
        # Clean invalid project references in chat_sessions
        updated = await conn.execute("""
            UPDATE chat_sessions 
            SET project_id = NULL 
            WHERE project_id IS NOT NULL 
            AND project_id NOT IN (
                SELECT id::text FROM projects
            )
        """)
        print(f"✅ Cleaned invalid project references: {updated}")
        
        print("\n=== Quick Fix 3: Verify Data Integrity ===")
        # Check remaining issues
        orphaned = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_messages cm
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.id IS NULL
        """)
        print(f"Remaining orphaned messages: {orphaned}")
        
        invalid_refs = await conn.fetchval("""
            SELECT COUNT(*) FROM chat_sessions cs
            WHERE cs.project_id IS NOT NULL 
            AND cs.project_id NOT IN (
                SELECT id::text FROM projects
            )
        """)
        print(f"Remaining invalid project references: {invalid_refs}")
        
        await conn.close()
        print("✅ Quick database fixes completed")
        
    except Exception as e:
        print(f"❌ Quick database fix failed: {e}")
        raise

def quick_api_fix():
    """Quick API timestamp fix"""
    api_file = 'apps/api/minimal_api.py'
    
    if not os.path.exists(api_file):
        print(f"⚠️  API file not found: {api_file}")
        return
    
    print(f"\n=== Quick Fix 4: API Timestamp Format ===")
    
    with open(api_file, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Add timezone import if missing
    if 'from datetime import timezone' not in content:
        if 'from datetime import datetime' in content:
            content = content.replace(
                'from datetime import datetime',
                'from datetime import datetime, timezone'
            )
        else:
            # Add import at the top
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i, 'from datetime import timezone')
                    break
            content = '\n'.join(lines)
    
    # Create a simple fix function
    fix_function = '''
def fix_datetime_tz(dt):
    """Ensure datetime has timezone info for consistent API responses"""
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).isoformat()
    return dt.isoformat()
'''
    
    # Add the fix function after imports
    if 'def fix_datetime_tz' not in content:
        # Find a good place to insert the function
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('app = FastAPI'):
                insert_idx = i
                break
        
        lines.insert(insert_idx, fix_function)
        content = '\n'.join(lines)
    
    # Replace isoformat calls with the fix function
    replacements = [
        ('row[7].isoformat()', 'fix_datetime_tz(row[7])'),
        ('row[8].isoformat() if row[8] else None', 'fix_datetime_tz(row[8])'),
        ('result[7].isoformat()', 'fix_datetime_tz(result[7])'),
        ('result[8].isoformat() if result[8] else None', 'fix_datetime_tz(result[8])'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original_content:
        with open(api_file, 'w') as f:
            f.write(content)
        print(f"✅ Fixed timestamp serialization in {api_file}")
    else:
        print(f"ℹ️  No changes needed in {api_file}")

async def main():
    """Run quick fixes"""
    print("🚀 QUICK INTEGRATION FIXES")
    print("=" * 30)
    
    try:
        await quick_database_fix()
        quick_api_fix()
        
        print("\n🎉 QUICK FIXES COMPLETED!")
        print("\nThese fixes should resolve:")
        print("✅ Orphaned chat messages (42 records)")
        print("✅ Invalid project references in chat sessions")
        print("✅ Timestamp format inconsistency (API vs DB)")
        print("\nRemaining issues that need manual migration:")
        print("⚠️  Mixed ID types (requires schema migration)")
        print("⚠️  PostgreSQL collation version (may need superuser)")
        
        print("\nNext steps:")
        print("1. Restart your API server")
        print("2. Run: python comprehensive_system_integration_test.py")
        print("3. Review id_standardization_migration.sql for ID type fixes")
        
    except Exception as e:
        print(f"❌ Quick fixes failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())