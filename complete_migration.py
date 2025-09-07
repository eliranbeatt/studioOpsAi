#!/usr/bin/env python3
"""
Complete the ID standardization migration by switching to new columns
"""

import asyncio
import asyncpg
import os

async def complete_migration():
    """Complete the migration by switching to new UUID columns"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database")
        
        print("🔄 Completing ID standardization migration...")
        
        # Step 1: Drop old columns and rename new ones
        await conn.execute("ALTER TABLE chat_sessions DROP COLUMN id CASCADE")
        await conn.execute("ALTER TABLE chat_sessions DROP COLUMN project_id")
        await conn.execute("ALTER TABLE chat_sessions RENAME COLUMN new_id TO id")
        await conn.execute("ALTER TABLE chat_sessions RENAME COLUMN new_project_id TO project_id")
        print("✅ Updated chat_sessions columns")
        
        await conn.execute("ALTER TABLE chat_messages DROP COLUMN id CASCADE")
        await conn.execute("ALTER TABLE chat_messages DROP COLUMN session_id")
        await conn.execute("ALTER TABLE chat_messages RENAME COLUMN new_id TO id")
        await conn.execute("ALTER TABLE chat_messages RENAME COLUMN new_session_id TO session_id")
        print("✅ Updated chat_messages columns")
        
        # Step 2: Recreate constraints
        await conn.execute("ALTER TABLE chat_sessions ADD PRIMARY KEY (id)")
        await conn.execute("ALTER TABLE chat_messages ADD PRIMARY KEY (id)")
        await conn.execute("ALTER TABLE chat_messages ADD FOREIGN KEY (session_id) REFERENCES chat_sessions(id)")
        await conn.execute("ALTER TABLE chat_sessions ADD FOREIGN KEY (project_id) REFERENCES projects(id)")
        print("✅ Recreated constraints")
        
        # Step 3: Drop backup tables
        await conn.execute("DROP TABLE chat_sessions_backup")
        await conn.execute("DROP TABLE chat_messages_backup")
        print("✅ Cleaned up backup tables")
        
        # Verify final state
        print("\n📊 Final Verification:")
        
        # Check ID types
        sessions_id_type = await conn.fetchval("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'chat_sessions' AND column_name = 'id'
        """)
        messages_id_type = await conn.fetchval("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'chat_messages' AND column_name = 'id'
        """)
        project_id_type = await conn.fetchval("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'chat_sessions' AND column_name = 'project_id'
        """)
        
        print(f"chat_sessions.id: {sessions_id_type}")
        print(f"chat_messages.id: {messages_id_type}")
        print(f"chat_sessions.project_id: {project_id_type}")
        
        await conn.close()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration completion failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(complete_migration())