#!/usr/bin/env python3
"""
Database Migration Script for Foreign Key Constraint Fixes
Task 8: Database Migration and Schema Updates

This script implements the database migration for foreign key constraint fixes
and provides comprehensive database health monitoring and validation.
"""

import psycopg2
import psycopg2.extras
import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseMigrationService:
    """Service for managing database migrations and health monitoring"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'postgresql://studioops:studioops123@localhost:5432/studioops'
        )
        self.migration_results = {}
        
    def get_connection(self):
        """Get database connection with error handling"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "connection": {"status": "disconnected"},
            "tables": {"status": "unknown", "details": {}},
            "foreign_keys": {"status": "unknown", "details": {}},
            "indexes": {"status": "unknown", "details": {}},
            "data_integrity": {"status": "unknown", "details": {}},
            "performance": {"status": "unknown", "details": {}},
            "warnings": [],
            "errors": []
        }
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # 1. Test basic connectivity
                    cur.execute("SELECT version(), current_database(), current_user;")
                    db_info = cur.fetchone()
                    health_status["connection"] = {
                        "status": "connected",
                        "database": db_info["current_database"],
                        "user": db_info["current_user"],
                        "version": db_info["version"][:50] + "..."
                    }
                    
                    # 2. Check table existence and structure
                    required_tables = [
                        'projects', 'plans', 'plan_items', 'vendors', 'materials',
                        'vendor_prices', 'purchases', 'chat_sessions', 'chat_messages',
                        'documents', 'rag_documents'
                    ]
                    
                    cur.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                        ORDER BY table_name;
                    """)
                    existing_tables = [row["table_name"] for row in cur.fetchall()]
                    
                    missing_tables = [t for t in required_tables if t not in existing_tables]
                    extra_tables = [t for t in existing_tables if t not in required_tables]
                    
                    health_status["tables"] = {
                        "status": "healthy" if not missing_tables else "degraded",
                        "details": {
                            "total_tables": len(existing_tables),
                            "required_tables": len(required_tables),
                            "missing_tables": missing_tables,
                            "extra_tables": extra_tables,
                            "all_tables": existing_tables
                        }
                    }
                    
                    if missing_tables:
                        health_status["warnings"].append(f"Missing tables: {missing_tables}")
                    
                    # 3. Check foreign key constraints
                    cur.execute("""
                        SELECT 
                            tc.table_name, 
                            kcu.column_name, 
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name,
                            tc.constraint_name,
                            rc.delete_rule
                        FROM 
                            information_schema.table_constraints AS tc 
                            JOIN information_schema.key_column_usage AS kcu
                                ON tc.constraint_name = kcu.constraint_name
                            JOIN information_schema.constraint_column_usage AS ccu
                                ON ccu.constraint_name = tc.constraint_name
                            JOIN information_schema.referential_constraints AS rc
                                ON tc.constraint_name = rc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY' 
                            AND tc.table_schema = 'public'
                        ORDER BY tc.table_name, kcu.column_name;
                    """)
                    
                    foreign_keys = cur.fetchall()
                    project_related_fks = [
                        fk for fk in foreign_keys 
                        if 'project' in fk["table_name"] or 'project' in fk["column_name"]
                    ]
                    
                    # Check if critical foreign keys have proper DELETE rules
                    critical_fk_rules = {
                        "chat_sessions.project_id": "SET NULL",
                        "documents.project_id": "SET NULL", 
                        "purchases.project_id": "SET NULL",
                        "plans.project_id": "CASCADE"
                    }
                    
                    fk_issues = []
                    for fk in foreign_keys:
                        fk_key = f"{fk['table_name']}.{fk['column_name']}"
                        if fk_key in critical_fk_rules:
                            expected_rule = critical_fk_rules[fk_key]
                            if fk["delete_rule"] != expected_rule:
                                fk_issues.append(f"{fk_key} has {fk['delete_rule']}, expected {expected_rule}")
                    
                    health_status["foreign_keys"] = {
                        "status": "healthy" if not fk_issues else "degraded",
                        "details": {
                            "total_foreign_keys": len(foreign_keys),
                            "project_related_fks": len(project_related_fks),
                            "issues": fk_issues,
                            "all_foreign_keys": [
                                f"{fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']} [{fk['delete_rule']}]"
                                for fk in foreign_keys
                            ]
                        }
                    }
                    
                    if fk_issues:
                        health_status["warnings"].extend(fk_issues)
                    
                    # 4. Check indexes
                    cur.execute("""
                        SELECT 
                            schemaname, tablename, indexname, indexdef
                        FROM pg_indexes 
                        WHERE schemaname = 'public'
                        ORDER BY tablename, indexname;
                    """)
                    indexes = cur.fetchall()
                    
                    health_status["indexes"] = {
                        "status": "healthy",
                        "details": {
                            "total_indexes": len(indexes),
                            "indexes_by_table": {}
                        }
                    }
                    
                    # Group indexes by table
                    for idx in indexes:
                        table = idx["tablename"]
                        if table not in health_status["indexes"]["details"]["indexes_by_table"]:
                            health_status["indexes"]["details"]["indexes_by_table"][table] = []
                        health_status["indexes"]["details"]["indexes_by_table"][table].append(idx["indexname"])
                    
                    # 5. Basic data integrity checks
                    data_integrity_results = {}
                    
                    # Check for orphaned records
                    if 'projects' in existing_tables and 'plans' in existing_tables:
                        cur.execute("""
                            SELECT COUNT(*) as count FROM plans 
                            WHERE project_id NOT IN (SELECT id::text FROM projects);
                        """)
                        orphaned_plans = cur.fetchone()["count"]
                        data_integrity_results["orphaned_plans"] = orphaned_plans
                        
                        if orphaned_plans > 0:
                            health_status["warnings"].append(f"Found {orphaned_plans} orphaned plans")
                    
                    # Check for NULL foreign keys where they shouldn't be
                    if 'plan_items' in existing_tables:
                        cur.execute("SELECT COUNT(*) as count FROM plan_items WHERE plan_id IS NULL;")
                        plan_items_no_plan = cur.fetchone()["count"]
                        data_integrity_results["plan_items_without_plan"] = plan_items_no_plan
                        
                        if plan_items_no_plan > 0:
                            health_status["warnings"].append(f"Found {plan_items_no_plan} plan items without plan")
                    
                    health_status["data_integrity"] = {
                        "status": "healthy" if not health_status["warnings"] else "degraded",
                        "details": data_integrity_results
                    }
                    
                    # 6. Performance metrics
                    performance_metrics = {}
                    
                    # Database size
                    cur.execute("SELECT pg_size_pretty(pg_database_size(current_database())) as size;")
                    db_size = cur.fetchone()["size"]
                    performance_metrics["database_size"] = db_size
                    
                    # Table sizes
                    cur.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY size_bytes DESC;
                    """)
                    table_sizes = cur.fetchall()
                    performance_metrics["table_sizes"] = [
                        {"table": row["tablename"], "size": row["size"]} 
                        for row in table_sizes[:10]  # Top 10 largest tables
                    ]
                    
                    # Connection count
                    cur.execute("SELECT count(*) as connections FROM pg_stat_activity;")
                    connections = cur.fetchone()["connections"]
                    performance_metrics["active_connections"] = connections
                    
                    health_status["performance"] = {
                        "status": "healthy",
                        "details": performance_metrics
                    }
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["overall_status"] = "unhealthy"
            health_status["errors"].append(str(e))
            health_status["connection"]["status"] = "failed"
        
        # Determine overall status
        if health_status["errors"]:
            health_status["overall_status"] = "unhealthy"
        elif health_status["warnings"]:
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "healthy"
        
        return health_status
    
    def fix_foreign_key_constraints(self) -> Dict[str, Any]:
        """Fix foreign key constraints with proper DELETE actions"""
        logger.info("Starting foreign key constraint fixes...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "constraints_fixed": [],
            "constraints_already_correct": [],
            "errors": [],
            "rollback_info": []
        }
        
        # Define the required constraint fixes
        constraint_fixes = [
            {
                "table": "chat_sessions",
                "column": "project_id",
                "referenced_table": "projects", 
                "referenced_column": "id",
                "delete_rule": "SET NULL",
                "constraint_name": "chat_sessions_project_id_fkey"
            },
            {
                "table": "documents",
                "column": "project_id", 
                "referenced_table": "projects",
                "referenced_column": "id",
                "delete_rule": "SET NULL",
                "constraint_name": "documents_project_id_fkey"
            },
            {
                "table": "purchases",
                "column": "project_id",
                "referenced_table": "projects",
                "referenced_column": "id", 
                "delete_rule": "SET NULL",
                "constraint_name": "purchases_project_id_fkey"
            },
            {
                "table": "plans",
                "column": "project_id",
                "referenced_table": "projects",
                "referenced_column": "id",
                "delete_rule": "CASCADE",
                "constraint_name": "plans_project_id_fkey"
            }
        ]
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check current constraints
                    cur.execute("""
                        SELECT 
                            tc.table_name,
                            kcu.column_name, 
                            tc.constraint_name,
                            rc.delete_rule
                        FROM 
                            information_schema.table_constraints AS tc 
                            JOIN information_schema.key_column_usage AS kcu
                                ON tc.constraint_name = kcu.constraint_name
                            JOIN information_schema.referential_constraints AS rc
                                ON tc.constraint_name = rc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY' 
                            AND tc.table_schema = 'public';
                    """)
                    
                    current_constraints = {
                        f"{row[0]}.{row[1]}": {"name": row[2], "delete_rule": row[3]}
                        for row in cur.fetchall()
                    }
                    
                    for fix in constraint_fixes:
                        constraint_key = f"{fix['table']}.{fix['column']}"
                        
                        if constraint_key in current_constraints:
                            current_rule = current_constraints[constraint_key]["delete_rule"]
                            current_name = current_constraints[constraint_key]["name"]
                            
                            if current_rule == fix["delete_rule"]:
                                results["constraints_already_correct"].append({
                                    "constraint": constraint_key,
                                    "rule": current_rule
                                })
                                logger.info(f"Constraint {constraint_key} already has correct DELETE rule: {current_rule}")
                                continue
                            
                            # Need to fix this constraint
                            logger.info(f"Fixing constraint {constraint_key}: {current_rule} -> {fix['delete_rule']}")
                            
                            try:
                                # Drop existing constraint
                                drop_sql = f"ALTER TABLE {fix['table']} DROP CONSTRAINT IF EXISTS {current_name};"
                                cur.execute(drop_sql)
                                
                                # Create new constraint with correct DELETE rule
                                create_sql = f"""
                                    ALTER TABLE {fix['table']} 
                                    ADD CONSTRAINT {fix['constraint_name']} 
                                    FOREIGN KEY ({fix['column']}) 
                                    REFERENCES {fix['referenced_table']}({fix['referenced_column']}) 
                                    ON DELETE {fix['delete_rule']};
                                """
                                cur.execute(create_sql)
                                
                                results["constraints_fixed"].append({
                                    "constraint": constraint_key,
                                    "old_rule": current_rule,
                                    "new_rule": fix["delete_rule"],
                                    "rollback_sql": f"ALTER TABLE {fix['table']} DROP CONSTRAINT {fix['constraint_name']}; ALTER TABLE {fix['table']} ADD CONSTRAINT {current_name} FOREIGN KEY ({fix['column']}) REFERENCES {fix['referenced_table']}({fix['referenced_column']}) ON DELETE {current_rule};"
                                })
                                
                                logger.info(f"Successfully fixed constraint {constraint_key}")
                                
                            except Exception as e:
                                error_msg = f"Failed to fix constraint {constraint_key}: {e}"
                                logger.error(error_msg)
                                results["errors"].append(error_msg)
                                # Continue with other constraints
                        else:
                            # Constraint doesn't exist, create it
                            logger.info(f"Creating missing constraint {constraint_key}")
                            
                            try:
                                create_sql = f"""
                                    ALTER TABLE {fix['table']} 
                                    ADD CONSTRAINT {fix['constraint_name']} 
                                    FOREIGN KEY ({fix['column']}) 
                                    REFERENCES {fix['referenced_table']}({fix['referenced_column']}) 
                                    ON DELETE {fix['delete_rule']};
                                """
                                cur.execute(create_sql)
                                
                                results["constraints_fixed"].append({
                                    "constraint": constraint_key,
                                    "old_rule": "NOT_EXISTS",
                                    "new_rule": fix["delete_rule"],
                                    "rollback_sql": f"ALTER TABLE {fix['table']} DROP CONSTRAINT {fix['constraint_name']};"
                                })
                                
                                logger.info(f"Successfully created constraint {constraint_key}")
                                
                            except Exception as e:
                                error_msg = f"Failed to create constraint {constraint_key}: {e}"
                                logger.error(error_msg)
                                results["errors"].append(error_msg)
                    
                    # Commit changes if no errors
                    if not results["errors"]:
                        conn.commit()
                        results["success"] = True
                        logger.info("All foreign key constraint fixes committed successfully")
                    else:
                        conn.rollback()
                        logger.error("Rolling back due to errors in constraint fixes")
        
        except Exception as e:
            error_msg = f"Critical error during foreign key constraint fixes: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def create_database_backup(self) -> Dict[str, Any]:
        """Create a database backup before migrations"""
        logger.info("Creating database backup...")
        
        backup_result = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "backup_location": None,
            "backup_size": None,
            "errors": []
        }
        
        try:
            # For this implementation, we'll create a schema backup
            backup_filename = f"studioops_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            backup_path = os.path.join(os.getcwd(), backup_filename)
            
            # Use pg_dump to create backup
            import subprocess
            
            # Extract connection parameters
            db_url_parts = self.database_url.replace("postgresql://", "").split("@")
            user_pass = db_url_parts[0].split(":")
            host_db = db_url_parts[1].split("/")
            host_port = host_db[0].split(":")
            
            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ""
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
            database = host_db[1]
            
            # Set environment variables for pg_dump
            env = os.environ.copy()
            if password:
                env["PGPASSWORD"] = password
            
            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", database,
                "--schema-only",  # Schema only for this migration
                "-f", backup_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                backup_size = os.path.getsize(backup_path)
                backup_result.update({
                    "success": True,
                    "backup_location": backup_path,
                    "backup_size": backup_size
                })
                logger.info(f"Database backup created: {backup_path} ({backup_size} bytes)")
            else:
                backup_result["errors"].append(f"pg_dump failed: {result.stderr}")
                logger.error(f"pg_dump failed: {result.stderr}")
        
        except Exception as e:
            error_msg = f"Backup creation failed: {e}"
            backup_result["errors"].append(error_msg)
            logger.error(error_msg)
        
        return backup_result
    
    def run_migration(self, create_backup: bool = True) -> Dict[str, Any]:
        """Run the complete database migration"""
        logger.info("Starting database migration for Task 8...")
        
        migration_result = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "backup": None,
            "health_check_before": None,
            "foreign_key_fixes": None,
            "health_check_after": None,
            "errors": [],
            "duration_seconds": 0
        }
        
        start_time = time.time()
        
        try:
            # 1. Pre-migration health check
            logger.info("Running pre-migration health check...")
            migration_result["health_check_before"] = self.check_database_health()
            
            # 2. Create backup if requested
            if create_backup:
                migration_result["backup"] = self.create_database_backup()
                if not migration_result["backup"]["success"]:
                    logger.warning("Backup failed, but continuing with migration...")
            
            # 3. Fix foreign key constraints
            migration_result["foreign_key_fixes"] = self.fix_foreign_key_constraints()
            
            # 4. Post-migration health check
            logger.info("Running post-migration health check...")
            migration_result["health_check_after"] = self.check_database_health()
            
            # 5. Determine overall success
            if (migration_result["foreign_key_fixes"]["success"] and 
                migration_result["health_check_after"]["overall_status"] in ["healthy", "degraded"]):
                migration_result["success"] = True
                logger.info("Database migration completed successfully!")
            else:
                migration_result["errors"].append("Migration completed with errors")
                logger.error("Migration completed with errors")
        
        except Exception as e:
            error_msg = f"Migration failed with critical error: {e}"
            migration_result["errors"].append(error_msg)
            logger.error(error_msg)
        
        finally:
            migration_result["duration_seconds"] = time.time() - start_time
        
        return migration_result


def main():
    """Main function to run the database migration"""
    print("=" * 80)
    print("StudioOps AI - Database Migration Script")
    print("Task 8: Database Migration and Schema Updates")
    print("=" * 80)
    
    migration_service = DatabaseMigrationService()
    
    # Run the migration
    result = migration_service.run_migration(create_backup=True)
    
    # Print results
    print("\nMigration Results:")
    print("=" * 40)
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration_seconds']:.2f} seconds")
    
    if result["foreign_key_fixes"]:
        fk_fixes = result["foreign_key_fixes"]
        print(f"\nForeign Key Fixes:")
        print(f"  Fixed: {len(fk_fixes['constraints_fixed'])}")
        print(f"  Already Correct: {len(fk_fixes['constraints_already_correct'])}")
        print(f"  Errors: {len(fk_fixes['errors'])}")
    
    if result["health_check_after"]:
        health = result["health_check_after"]
        print(f"\nPost-Migration Health:")
        print(f"  Overall Status: {health['overall_status']}")
        print(f"  Tables: {health['tables']['status']}")
        print(f"  Foreign Keys: {health['foreign_keys']['status']}")
        print(f"  Data Integrity: {health['data_integrity']['status']}")
    
    if result["errors"]:
        print(f"\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")
    
    # Save detailed results to file
    results_file = f"migration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return result["success"]


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)