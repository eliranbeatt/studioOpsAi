#!/usr/bin/env python3
"""Test script for MCP server database connectivity"""

import asyncio
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')

async def test_database_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        
        print(f"Database connection successful!")
        print(f"Found {table_count} tables in public schema")
        
        # List available tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {tables}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def test_mcp_queries():
    """Test MCP-style queries"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test projects query
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        print(f"Found {project_count} projects in database")
        
        # Test sample project data
        cursor.execute("SELECT id, name, status FROM projects ORDER BY created_at DESC LIMIT 3")
        projects = cursor.fetchall()
        
        for project in projects:
            print(f"   - {project[1]} ({project[2]}) - ID: {project[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"MCP query test failed: {e}")
        return False

async def main():
    print("Testing PostgreSQL MCP Server Database Connectivity")
    print("=" * 60)
    
    # Test database connection
    success1 = await test_database_connection()
    print()
    
    # Test MCP queries
    success2 = await test_mcp_queries()
    print()
    
    if success1 and success2:
        print("All tests passed! MCP server should work correctly.")
    else:
        print("Some tests failed. Please check database configuration.")

if __name__ == "__main__":
    asyncio.run(main())