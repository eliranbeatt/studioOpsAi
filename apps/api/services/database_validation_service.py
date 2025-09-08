"""
Database Validation Service
Provides comprehensive data integrity checks and validation functions
Requirements: 1.6, 5.4, 6.2
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Project, Plan, PlanItem, Document, Purchase, ChatSession

logger = logging.getLogger(__name__)

class DatabaseValidationService:
    """Service for validating database integrity and constraints"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_results = []
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all database validation checks"""
        logger.info("Starting comprehensive database validation")
        
        validation_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "checks": {},
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # 1. Foreign key constraint validation
            validation_report["checks"]["foreign_keys"] = await self._validate_foreign_key_constraints()
            
            # 2. Data integrity validation
            validation_report["checks"]["data_integrity"] = await self._validate_data_integrity()
            
            # 3. Orphaned records validation
            validation_report["checks"]["orphaned_records"] = await self._validate_orphaned_records()
            
            # 4. Schema consistency validation
            validation_report["checks"]["schema_consistency"] = await self._validate_schema_consistency()
            
            # 5. Index and performance validation
            validation_report["checks"]["performance"] = await self._validate_performance_indexes()
            
            # Determine overall status
            validation_report["overall_status"] = self._determine_overall_status(validation_report["checks"])
            
            logger.info(f"Database validation completed with status: {validation_report['overall_status']}")
            
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            validation_report["overall_status"] = "error"
            validation_report["errors"].append(f"Validation process failed: {str(e)}")
        
        return validation_report
    
    async def _validate_foreign_key_constraints(self) -> Dict[str, Any]:
        """Validate all foreign key constraints are properly configured"""
        logger.info("Validating foreign key constraints")
        
        result = {
            "status": "success",
            "constraints_checked": 0,
            "issues_found": 0,
            "details": []
        }
        
        try:
            # Check chat_sessions foreign key
            constraint_info = await self._check_constraint_details("chat_sessions", "project_id", "projects", "id")
            result["details"].append(constraint_info)
            result["constraints_checked"] += 1
            
            if constraint_info["delete_action"] != "SET NULL":
                result["issues_found"] += 1
                result["details"][-1]["issue"] = f"Expected ON DELETE SET NULL, found {constraint_info['delete_action']}"
            
            # Check documents foreign key
            constraint_info = await self._check_constraint_details("documents", "project_id", "projects", "id")
            result["details"].append(constraint_info)
            result["constraints_checked"] += 1
            
            if constraint_info["delete_action"] != "SET NULL":
                result["issues_found"] += 1
                result["details"][-1]["issue"] = f"Expected ON DELETE SET NULL, found {constraint_info['delete_action']}"
            
            # Check purchases foreign key
            constraint_info = await self._check_constraint_details("purchases", "project_id", "projects", "id")
            result["details"].append(constraint_info)
            result["constraints_checked"] += 1
            
            if constraint_info["delete_action"] != "SET NULL":
                result["issues_found"] += 1
                result["details"][-1]["issue"] = f"Expected ON DELETE SET NULL, found {constraint_info['delete_action']}"
            
            # Check plans foreign key
            constraint_info = await self._check_constraint_details("plans", "project_id", "projects", "id")
            result["details"].append(constraint_info)
            result["constraints_checked"] += 1
            
            if constraint_info["delete_action"] != "CASCADE":
                result["issues_found"] += 1
                result["details"][-1]["issue"] = f"Expected ON DELETE CASCADE, found {constraint_info['delete_action']}"
            
            # Check plan_items foreign key
            constraint_info = await self._check_constraint_details("plan_items", "plan_id", "plans", "id")
            result["details"].append(constraint_info)
            result["constraints_checked"] += 1
            
            if constraint_info["delete_action"] != "CASCADE":
                result["issues_found"] += 1
                result["details"][-1]["issue"] = f"Expected ON DELETE CASCADE, found {constraint_info['delete_action']}"
            
            if result["issues_found"] > 0:
                result["status"] = "warning"
            
        except Exception as e:
            logger.error(f"Foreign key validation failed: {e}")
            result["status"] = "error"
            result["details"].append({"error": str(e)})
        
        return result
    
    async def _check_constraint_details(self, table_name: str, column_name: str, 
                                      ref_table: str, ref_column: str) -> Dict[str, Any]:
        """Check details of a specific foreign key constraint"""
        
        query = text("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
                  AND tc.table_schema = rc.constraint_schema
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = :table_name
                AND kcu.column_name = :column_name
                AND ccu.table_name = :ref_table
                AND ccu.column_name = :ref_column
        """)
        
        result = self.db.execute(query, {
            "table_name": table_name,
            "column_name": column_name,
            "ref_table": ref_table,
            "ref_column": ref_column
        }).fetchone()
        
        if result:
            return {
                "constraint_name": result.constraint_name,
                "table": result.table_name,
                "column": result.column_name,
                "references": f"{result.foreign_table_name}.{result.foreign_column_name}",
                "delete_action": result.delete_rule,
                "exists": True
            }
        else:
            return {
                "table": table_name,
                "column": column_name,
                "references": f"{ref_table}.{ref_column}",
                "delete_action": "NONE",
                "exists": False,
                "issue": "Foreign key constraint not found"
            }
    
    async def _validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across all tables"""
        logger.info("Validating data integrity")
        
        result = {
            "status": "success",
            "checks_performed": 0,
            "issues_found": 0,
            "details": []
        }
        
        try:
            # Check for NULL values in required fields
            null_checks = [
                ("projects", "id", "Project ID cannot be NULL"),
                ("projects", "name", "Project name cannot be NULL"),
                ("plans", "id", "Plan ID cannot be NULL"),
                ("plan_items", "id", "Plan item ID cannot be NULL"),
                ("documents", "id", "Document ID cannot be NULL"),
                ("chat_sessions", "id", "Chat session ID cannot be NULL")
            ]
            
            for table, column, description in null_checks:
                null_count = await self._count_null_values(table, column)
                result["checks_performed"] += 1
                
                if null_count > 0:
                    result["issues_found"] += 1
                    result["details"].append({
                        "type": "null_values",
                        "table": table,
                        "column": column,
                        "count": null_count,
                        "description": description
                    })
            
            # Check for invalid UUID formats
            uuid_checks = [
                ("projects", "id"),
                ("plans", "id"),
                ("plan_items", "id"),
                ("documents", "id"),
                ("chat_sessions", "id")
            ]
            
            for table, column in uuid_checks:
                invalid_uuid_count = await self._count_invalid_uuids(table, column)
                result["checks_performed"] += 1
                
                if invalid_uuid_count > 0:
                    result["issues_found"] += 1
                    result["details"].append({
                        "type": "invalid_uuid",
                        "table": table,
                        "column": column,
                        "count": invalid_uuid_count,
                        "description": f"Invalid UUID format in {table}.{column}"
                    })
            
            # Check for duplicate primary keys
            duplicate_checks = [
                ("projects", "id"),
                ("plans", "id"),
                ("plan_items", "id"),
                ("documents", "id"),
                ("chat_sessions", "id")
            ]
            
            for table, column in duplicate_checks:
                duplicate_count = await self._count_duplicate_values(table, column)
                result["checks_performed"] += 1
                
                if duplicate_count > 0:
                    result["issues_found"] += 1
                    result["details"].append({
                        "type": "duplicate_primary_key",
                        "table": table,
                        "column": column,
                        "count": duplicate_count,
                        "description": f"Duplicate primary keys in {table}.{column}"
                    })
            
            if result["issues_found"] > 0:
                result["status"] = "warning"
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            result["status"] = "error"
            result["details"].append({"error": str(e)})
        
        return result
    
    async def _validate_orphaned_records(self) -> Dict[str, Any]:
        """Check for orphaned records that reference non-existent parents"""
        logger.info("Validating orphaned records")
        
        result = {
            "status": "success",
            "checks_performed": 0,
            "orphaned_records": 0,
            "details": []
        }
        
        try:
            # Check for orphaned chat_sessions
            orphaned_chat_sessions = await self._count_orphaned_records(
                "chat_sessions", "project_id", "projects", "id"
            )
            result["checks_performed"] += 1
            
            if orphaned_chat_sessions > 0:
                result["orphaned_records"] += orphaned_chat_sessions
                result["details"].append({
                    "table": "chat_sessions",
                    "foreign_key": "project_id",
                    "count": orphaned_chat_sessions,
                    "description": "Chat sessions referencing non-existent projects"
                })
            
            # Check for orphaned documents
            orphaned_documents = await self._count_orphaned_records(
                "documents", "project_id", "projects", "id"
            )
            result["checks_performed"] += 1
            
            if orphaned_documents > 0:
                result["orphaned_records"] += orphaned_documents
                result["details"].append({
                    "table": "documents",
                    "foreign_key": "project_id",
                    "count": orphaned_documents,
                    "description": "Documents referencing non-existent projects"
                })
            
            # Check for orphaned purchases
            orphaned_purchases = await self._count_orphaned_records(
                "purchases", "project_id", "projects", "id"
            )
            result["checks_performed"] += 1
            
            if orphaned_purchases > 0:
                result["orphaned_records"] += orphaned_purchases
                result["details"].append({
                    "table": "purchases",
                    "foreign_key": "project_id",
                    "count": orphaned_purchases,
                    "description": "Purchases referencing non-existent projects"
                })
            
            # Check for orphaned plan_items
            orphaned_plan_items = await self._count_orphaned_records(
                "plan_items", "plan_id", "plans", "id"
            )
            result["checks_performed"] += 1
            
            if orphaned_plan_items > 0:
                result["orphaned_records"] += orphaned_plan_items
                result["details"].append({
                    "table": "plan_items",
                    "foreign_key": "plan_id",
                    "count": orphaned_plan_items,
                    "description": "Plan items referencing non-existent plans"
                })
            
            if result["orphaned_records"] > 0:
                result["status"] = "warning"
            
        except Exception as e:
            logger.error(f"Orphaned records validation failed: {e}")
            result["status"] = "error"
            result["details"].append({"error": str(e)})
        
        return result
    
    async def _validate_schema_consistency(self) -> Dict[str, Any]:
        """Validate schema consistency and required tables/columns"""
        logger.info("Validating schema consistency")
        
        result = {
            "status": "success",
            "tables_checked": 0,
            "missing_elements": 0,
            "details": []
        }
        
        try:
            required_tables = [
                "projects", "plans", "plan_items", "documents", 
                "purchases", "chat_sessions", "migration_log"
            ]
            
            for table_name in required_tables:
                table_exists = await self._check_table_exists(table_name)
                result["tables_checked"] += 1
                
                if not table_exists:
                    result["missing_elements"] += 1
                    result["details"].append({
                        "type": "missing_table",
                        "name": table_name,
                        "description": f"Required table {table_name} is missing"
                    })
            
            # Check for required columns in key tables
            required_columns = {
                "projects": ["id", "name", "created_at"],
                "plans": ["id", "project_id", "created_at"],
                "plan_items": ["id", "plan_id", "name"],
                "documents": ["id", "filename", "created_at"],
                "chat_sessions": ["id", "created_at"]
            }
            
            for table_name, columns in required_columns.items():
                for column_name in columns:
                    column_exists = await self._check_column_exists(table_name, column_name)
                    
                    if not column_exists:
                        result["missing_elements"] += 1
                        result["details"].append({
                            "type": "missing_column",
                            "table": table_name,
                            "column": column_name,
                            "description": f"Required column {table_name}.{column_name} is missing"
                        })
            
            if result["missing_elements"] > 0:
                result["status"] = "error"
            
        except Exception as e:
            logger.error(f"Schema consistency validation failed: {e}")
            result["status"] = "error"
            result["details"].append({"error": str(e)})
        
        return result
    
    async def _validate_performance_indexes(self) -> Dict[str, Any]:
        """Validate that required indexes exist for performance"""
        logger.info("Validating performance indexes")
        
        result = {
            "status": "success",
            "indexes_checked": 0,
            "missing_indexes": 0,
            "recommendations": []
        }
        
        try:
            # Check for indexes on foreign key columns
            foreign_key_columns = [
                ("chat_sessions", "project_id"),
                ("documents", "project_id"),
                ("purchases", "project_id"),
                ("plans", "project_id"),
                ("plan_items", "plan_id")
            ]
            
            for table_name, column_name in foreign_key_columns:
                has_index = await self._check_column_index(table_name, column_name)
                result["indexes_checked"] += 1
                
                if not has_index:
                    result["missing_indexes"] += 1
                    result["recommendations"].append({
                        "type": "missing_index",
                        "table": table_name,
                        "column": column_name,
                        "recommendation": f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});"
                    })
            
            # Check for indexes on commonly queried columns
            common_query_columns = [
                ("projects", "created_at"),
                ("documents", "created_at"),
                ("chat_sessions", "created_at"),
                ("plans", "created_at")
            ]
            
            for table_name, column_name in common_query_columns:
                has_index = await self._check_column_index(table_name, column_name)
                result["indexes_checked"] += 1
                
                if not has_index:
                    result["recommendations"].append({
                        "type": "performance_index",
                        "table": table_name,
                        "column": column_name,
                        "recommendation": f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});"
                    })
            
            if result["missing_indexes"] > 0:
                result["status"] = "warning"
            
        except Exception as e:
            logger.error(f"Performance index validation failed: {e}")
            result["status"] = "error"
            result["recommendations"].append({"error": str(e)})
        
        return result
    
    # Helper methods for validation checks
    
    async def _count_null_values(self, table_name: str, column_name: str) -> int:
        """Count NULL values in a specific column"""
        query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL")
        result = self.db.execute(query).scalar()
        return result or 0
    
    async def _count_invalid_uuids(self, table_name: str, column_name: str) -> int:
        """Count invalid UUID values in a specific column"""
        query = text(f"""
            SELECT COUNT(*) FROM {table_name} 
            WHERE {column_name} IS NOT NULL 
            AND {column_name} !~ '^[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$'
        """)
        result = self.db.execute(query).scalar()
        return result or 0
    
    async def _count_duplicate_values(self, table_name: str, column_name: str) -> int:
        """Count duplicate values in a specific column"""
        query = text(f"""
            SELECT COUNT(*) FROM (
                SELECT {column_name} FROM {table_name} 
                GROUP BY {column_name} 
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        result = self.db.execute(query).scalar()
        return result or 0
    
    async def _count_orphaned_records(self, child_table: str, child_column: str, 
                                    parent_table: str, parent_column: str) -> int:
        """Count orphaned records that reference non-existent parents"""
        query = text(f"""
            SELECT COUNT(*) FROM {child_table} c
            LEFT JOIN {parent_table} p ON c.{child_column} = p.{parent_column}
            WHERE c.{child_column} IS NOT NULL AND p.{parent_column} IS NULL
        """)
        result = self.db.execute(query).scalar()
        return result or 0
    
    async def _check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = :table_name
            )
        """)
        result = self.db.execute(query, {"table_name": table_name}).scalar()
        return bool(result)
    
    async def _check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = :table_name AND column_name = :column_name
            )
        """)
        result = self.db.execute(query, {
            "table_name": table_name, 
            "column_name": column_name
        }).scalar()
        return bool(result)
    
    async def _check_column_index(self, table_name: str, column_name: str) -> bool:
        """Check if a column has an index"""
        query = text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename = :table_name 
                AND indexdef LIKE '%' || :column_name || '%'
            )
        """)
        result = self.db.execute(query, {
            "table_name": table_name,
            "column_name": column_name
        }).scalar()
        return bool(result)
    
    def _determine_overall_status(self, checks: Dict[str, Dict]) -> str:
        """Determine overall validation status based on individual check results"""
        has_errors = any(check.get("status") == "error" for check in checks.values())
        has_warnings = any(check.get("status") == "warning" for check in checks.values())
        
        if has_errors:
            return "error"
        elif has_warnings:
            return "warning"
        else:
            return "success"


# Standalone validation functions for use in scripts
async def run_database_validation(db: Session) -> Dict[str, Any]:
    """Run comprehensive database validation"""
    service = DatabaseValidationService(db)
    return await service.run_comprehensive_validation()


async def validate_foreign_keys_only(db: Session) -> Dict[str, Any]:
    """Run only foreign key constraint validation"""
    service = DatabaseValidationService(db)
    return await service._validate_foreign_key_constraints()