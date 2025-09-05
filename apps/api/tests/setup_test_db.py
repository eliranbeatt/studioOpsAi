#!/usr/bin/env python3
"""
Script to set up test database for testing
"""
import os
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load test environment
load_dotenv('.env.test')

async def setup_test_database():
    """Set up test database with schema"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    # Extract database name from URL
    db_name = database_url.split('/')[-1]
    base_url = database_url.rsplit('/', 1)[0] + '/postgres'
    
    # Connect to default database to create test database
    engine = create_engine(base_url)
    
    try:
        # Drop existing test database if it exists
        with engine.connect() as conn:
            conn.execute(text(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{db_name}' AND pid <> pg_backend_pid()"))
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            conn.commit()
        
        print(f"Created test database: {db_name}")
        
        # Now connect to test database and run migrations
        test_engine = create_engine(database_url)
        
        # TODO: Run actual database migrations here
        # For now, create basic tables
        with test_engine.connect() as conn:
            # Create projects table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'planned',
                    budget DECIMAL(15, 2),
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create vendors table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vendors (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    contact VARCHAR(255),
                    rating DECIMAL(3, 2),
                    specialty VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create materials table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS materials (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    unit VARCHAR(50),
                    unit_price DECIMAL(15, 2),
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()
        
        print("Test database schema created successfully")
        
    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    asyncio.run(setup_test_database())