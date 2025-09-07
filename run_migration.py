#!/usr/bin/env python3
"""
Run database migration for ID standardization
"""

import asyncio
import asyncpg
import os

async def run_migration():
    """Run the ID standardization migration"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
    
    # Read migration SQL
    with open('id_standardization_migration.sql', 'r') as f:
        migration_sql = f.read()
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        print("🔄 Running ID standardization migration...")
        
        # Execute migration
        await conn.execute(migration_sql)
        print("✅ Migration completed successfully")
        
        # Verify migration results
        print("\n📊 Migration Results:")
        
        # Check new columns exist
        sessions_cols = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_sessions' 
            AND column_name IN ('new_id', 'new_project_id')
        """)
        print(f"Chat sessions new columns: {dict(sessions_cols)}")
        
        messages_cols = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' 
            AND column_name IN ('new_id', 'new_session_id')
        """)
        print(f"Chat messages new columns: {dict(messages_cols)}")
        
        # Check data migration
        sessions_count = await conn.fetchval("SELECT COUNT(*) FROM chat_sessions")
        messages_count = await conn.fetchval("SELECT COUNT(*) FROM chat_messages")
        print(f"Sessions: {sessions_count}, Messages: {messages_count}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())