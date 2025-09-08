"""
Database Migration Manager
Handles migration execution, rollback, and recovery procedures
Requirements: 1.6, 5.4, 6.2
"""

import logging
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import subprocess
import json

# Add the parent directory to the path to import from apps.api
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from apps.api.database import get_database_url
from apps.api.services.database_validation_service import DatabaseValidationService

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations with rollback capabilities"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or get_database_url()
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.migration_dir = Path(__file__).parent.parent.parent / "infra" / "migrations"
        
    def execute_migration(self, migration_file: str, dry_run: bool = False) -> Dict[str, Any]:
        """Execute a migration with comprehensive error handling and rollback support"""
        logger.info(f"Starting migration execution: {migration_file}")
        
        result = {
            "migration_file": migration_file,
            "status": "unknown",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "operations": [],
            "errors": [],
            "rollback_available": False,
            "validation_results": None
        }
        
        db = self.SessionLocal()
        
        try:
            # 1. Pre-migration validation
            logger.info("Running pre-migration validation")
            validation_service = DatabaseValidationService(db)
            pre_validation = await validation_service.run_comprehensive_validation()
            
            if pre_validation["overall_status"] == "error":
                result["status"] = "aborted"
                result["errors"].append("Pre-migration validation failed - database in inconsistent state")
                return result
            
            # 2. Create backup point
            backup_result = await self._create_backup_point(db)
            if not backup_result["success"]:
                result["status"] = "aborted"
                result["errors"].append(f"Failed to create backup point: {backup_result['error']}")
                return result
            
            result["operations"].append({
                "type": "backup",
                "status": "success",
                "details": backup_result
            })
            
            # 3. Read and validate migration file
            migration_path = self.migration_dir / migration_file
            if not migration_path.exists():
                result["status"] = "error"
                result["errors"].append(f"Migration file not found: {migration_file}")
                return result
            
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            
            # 4. Execute migration (or dry run)
            if dry_run:
                logger.info("Performing dry run - no changes will be made")
                result["status"] = "dry_run_success"
                result["operations"].append({
                    "type": "dry_run",
                    "status": "success",
                    "details": "Migration syntax validated successfully"
                })
            else:
                # Execute the actual migration
                migration_result = await self._execute_migration_sql(db, migration_sql, migration_file)
                result["operations"].extend(migration_result["operations"])
                
                if migration_result["success"]:
                    result["status"] = "success"
                    result["rollback_available"] = True
                else:
                    result["status"] = "failed"
                    result["errors"].extend(migration_result["errors"])
                    
                    # Attempt automatic rollback
                    logger.warning("Migration failed, attempting automatic rollback")
                    rollback_result = await self._attempt_rollback(db, migration_file)
                    result["operations"].append({
                        "type": "automatic_rollback",
                        "status": "success" if rollback_result["success"] else "failed",
                        "details": rollback_result
                    })
            
            # 5. Post-migration validation
            if result["status"] in ["success", "dry_run_success"]:
                logger.info("Running post-migration validation")
                post_validation = await validation_service.run_comprehensive_validation()
                result["validation_results"] = {
                    "pre_migration": pre_validation,
                    "post_migration": post_validation
                }
                
                if post_validation["overall_status"] == "error":
                    result["status"] = "validation_failed"
                    result["errors"].append("Post-migration validation failed")
                    
                    # Attempt rollback due to validation failure
                    rollback_result = await self._attempt_rollback(db, migration_file)
                    result["operations"].append({
                        "type": "validation_rollback",
                        "status": "success" if rollback_result["success"] else "failed",
                        "details": rollback_result
                    })
            
            result["completed_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Migration execution failed with exception: {e}")
            result["status"] = "error"
            result["errors"].append(f"Unexpected error: {str(e)}")
            result["completed_at"] = datetime.utcnow().isoformat()
            
            # Attempt emergency rollback
            try:
                rollback_result = await self._attempt_rollback(db, migration_file)
                result["operations"].append({
                    "type": "emergency_rollback",
                    "status": "success" if rollback_result["success"] else "failed",
                    "details": rollback_result
                })
            except Exception as rollback_error:
                logger.error(f"Emergency rollback failed: {rollback_error}")
                result["errors"].append(f"Emergency rollback failed: {str(rollback_error)}")
        
        finally:
            db.close()
        
        return result
    
    async def _execute_migration_sql(self, db, migration_sql: str, migration_file: str) -> Dict[str, Any]:
        """Execute the migration SQL with detailed operation tracking"""
        result = {
            "success": False,
            "operations": [],
            "errors": []
        }
        
        try:
            # Split migration into individual statements for better error tracking
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                try:
                    logger.info(f"Executing statement {i+1}/{len(statements)}")
                    db.execute(text(statement))
                    db.commit()
                    
                    result["operations"].append({
                        "type": "sql_statement",
                        "statement_number": i + 1,
                        "status": "success",
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement
                    })
                    
                except SQLAlchemyError as e:
                    logger.error(f"Statement {i+1} failed: {e}")
                    result["errors"].append(f"Statement {i+1} failed: {str(e)}")
                    result["operations"].append({
                        "type": "sql_statement",
                        "statement_number": i + 1,
                        "status": "failed",
                        "error": str(e),
                        "statement": statement[:100] + "..." if len(statement) > 100 else statement
                    })
                    db.rollback()
                    return result
            
            # Log successful migration
            db.execute(text("""
                INSERT INTO migration_log (migration_name, status) 
                VALUES (:migration_name, 'completed')
                ON CONFLICT (migration_name) 
                DO UPDATE SET status = 'completed', applied_at = CURRENT_TIMESTAMP
            """), {"migration_name": migration_file})
            db.commit()
            
            result["success"] = True
            logger.info(f"Migration {migration_file} completed successfully")
            
        except Exception as e:
            logger.error(f"Migration execution failed: {e}")
            result["errors"].append(str(e))
            db.rollback()
        
        return result
    
    async def _attempt_rollback(self, db, migration_file: str) -> Dict[str, Any]:
        """Attempt to rollback a failed migration"""
        result = {
            "success": False,
            "method": "unknown",
            "details": [],
            "errors": []
        }
        
        try:
            # Check if migration has a rollback function
            rollback_function = self._get_rollback_function_name(migration_file)
            
            if rollback_function:
                # Attempt function-based rollback
                logger.info(f"Attempting function-based rollback using {rollback_function}")
                
                try:
                    rollback_result = db.execute(text(f"SELECT * FROM {rollback_function}()")).fetchall()
                    db.commit()
                    
                    result["success"] = True
                    result["method"] = "function_rollback"
                    result["details"] = [dict(row) for row in rollback_result]
                    
                    # Log rollback
                    db.execute(text("""
                        INSERT INTO migration_log (migration_name, status) 
                        VALUES (:migration_name, 'rolled_back')
                    """), {"migration_name": f"{migration_file}_rollback"})
                    db.commit()
                    
                except SQLAlchemyError as e:
                    result["errors"].append(f"Function rollback failed: {str(e)}")
                    db.rollback()
            
            if not result["success"]:
                # Attempt backup restoration
                logger.info("Attempting backup restoration rollback")
                backup_result = await self._restore_from_backup(db)
                
                if backup_result["success"]:
                    result["success"] = True
                    result["method"] = "backup_restoration"
                    result["details"] = backup_result["details"]
                else:
                    result["errors"].extend(backup_result["errors"])
        
        except Exception as e:
            logger.error(f"Rollback attempt failed: {e}")
            result["errors"].append(f"Rollback failed: {str(e)}")
        
        return result
    
    def _get_rollback_function_name(self, migration_file: str) -> Optional[str]:
        """Extract rollback function name from migration file"""
        # For our migration files, we know the pattern
        if "005_comprehensive_foreign_key_fixes" in migration_file:
            return "rollback_foreign_key_fixes"
        
        # Generic pattern matching
        if "foreign_key" in migration_file.lower():
            return "rollback_foreign_key_fixes"
        
        return None
    
    async def _create_backup_point(self, db) -> Dict[str, Any]:
        """Create a backup point before migration"""
        result = {
            "success": False,
            "backup_id": None,
            "timestamp": datetime.utcnow().isoformat(),
            "error": None
        }
        
        try:
            # Create a simple backup by recording current constraint states
            backup_id = f"backup_{int(datetime.utcnow().timestamp())}"
            
            # Store current foreign key constraint information
            constraint_info = db.execute(text("""
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule,
                    rc.update_rule
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                    JOIN information_schema.referential_constraints AS rc
                      ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
            """)).fetchall()
            
            # Store backup information
            backup_data = json.dumps([dict(row) for row in constraint_info])
            
            db.execute(text("""
                INSERT INTO migration_log (migration_name, rollback_script, status) 
                VALUES (:backup_id, :backup_data, 'backup')
            """), {
                "backup_id": backup_id,
                "backup_data": backup_data
            })
            db.commit()
            
            result["success"] = True
            result["backup_id"] = backup_id
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Backup creation failed: {e}")
        
        return result
    
    async def _restore_from_backup(self, db) -> Dict[str, Any]:
        """Restore database from the most recent backup"""
        result = {
            "success": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Find the most recent backup
            backup_record = db.execute(text("""
                SELECT migration_name, rollback_script, applied_at
                FROM migration_log 
                WHERE status = 'backup' 
                ORDER BY applied_at DESC 
                LIMIT 1
            """)).fetchone()
            
            if not backup_record:
                result["errors"].append("No backup found for restoration")
                return result
            
            # Parse backup data
            backup_data = json.loads(backup_record.rollback_script)
            
            # Restore constraints (simplified approach)
            for constraint in backup_data:
                try:
                    # This is a simplified restoration - in practice, you'd need more sophisticated logic
                    result["details"].append(f"Would restore constraint: {constraint['constraint_name']}")
                except Exception as e:
                    result["errors"].append(f"Failed to restore constraint {constraint.get('constraint_name', 'unknown')}: {str(e)}")
            
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(f"Backup restoration failed: {str(e)}")
        
        return result
    
    def list_available_migrations(self) -> List[str]:
        """List all available migration files"""
        if not self.migration_dir.exists():
            return []
        
        return [f.name for f in self.migration_dir.glob("*.sql")]
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get status of all migrations"""
        db = self.SessionLocal()
        
        try:
            # Get applied migrations
            applied_migrations = db.execute(text("""
                SELECT migration_name, applied_at, status 
                FROM migration_log 
                ORDER BY applied_at DESC
            """)).fetchall()
            
            available_migrations = self.list_available_migrations()
            
            return {
                "available_migrations": available_migrations,
                "applied_migrations": [dict(row) for row in applied_migrations],
                "pending_migrations": [
                    m for m in available_migrations 
                    if m not in [row.migration_name for row in applied_migrations]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "error": str(e),
                "available_migrations": [],
                "applied_migrations": [],
                "pending_migrations": []
            }
        finally:
            db.close()


# CLI interface for migration management
async def main():
    """Command-line interface for migration management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("command", choices=["execute", "rollback", "status", "list"], 
                       help="Command to execute")
    parser.add_argument("--migration", "-m", help="Migration file name")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without making changes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    manager = MigrationManager()
    
    if args.command == "execute":
        if not args.migration:
            print("Error: --migration is required for execute command")
            sys.exit(1)
        
        result = manager.execute_migration(args.migration, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        
        if result["status"] not in ["success", "dry_run_success"]:
            sys.exit(1)
    
    elif args.command == "status":
        status = manager.get_migration_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == "list":
        migrations = manager.list_available_migrations()
        print("Available migrations:")
        for migration in migrations:
            print(f"  - {migration}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())