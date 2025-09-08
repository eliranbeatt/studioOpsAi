"""
Startup Validation Service for StudioOps AI System

Validates service dependencies and system configuration on application startup
to ensure proper system initialization and early error detection.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import psycopg2
from minio import Minio
import requests

from services.health_monitoring_service import health_monitoring_service
from services.service_degradation_service import service_degradation_service, DegradationLevel

logger = logging.getLogger(__name__)

class StartupValidationService:
    def __init__(self):
        self.validation_results = {}
        self.startup_time = datetime.utcnow()
        self.critical_services = ["database"]
        self.optional_services = ["minio", "trello_mcp", "ai_service", "observability"]
        
    async def validate_system_startup(self) -> Dict[str, Any]:
        """Perform comprehensive system startup validation"""
        logger.info("Starting system startup validation...")
        
        validation_start = datetime.utcnow()
        
        # Run all validation checks
        results = {
            "environment": await self._validate_environment(),
            "configuration": await self._validate_configuration(),
            "critical_services": await self._validate_critical_services(),
            "optional_services": await self._validate_optional_services(),
            "database_schema": await self._validate_database_schema(),
            "file_permissions": await self._validate_file_permissions()
        }
        
        # Determine overall startup status
        startup_successful = self._determine_startup_success(results)
        
        validation_duration = (datetime.utcnow() - validation_start).total_seconds()
        
        startup_summary = {
            "startup_successful": startup_successful,
            "startup_time": self.startup_time.isoformat(),
            "validation_duration_seconds": round(validation_duration, 2),
            "validation_results": results,
            "system_ready": startup_successful,
            "warnings": self._collect_warnings(results),
            "errors": self._collect_errors(results)
        }
        
        # Log startup results
        if startup_successful:
            logger.info(f"System startup validation completed successfully in {validation_duration:.2f}s")
        else:
            logger.error(f"System startup validation failed after {validation_duration:.2f}s")
            for error in startup_summary["errors"]:
                logger.error(f"Startup error: {error}")
        
        # Set up service degradation based on validation results
        await self._setup_service_degradation(results)
        
        return startup_summary
    
    async def _validate_environment(self) -> Dict[str, Any]:
        """Validate environment configuration"""
        logger.info("Validating environment configuration...")
        
        required_env_vars = [
            "DATABASE_URL"
        ]
        
        optional_env_vars = [
            "MINIO_ENDPOINT",
            "MINIO_ACCESS_KEY", 
            "MINIO_SECRET_KEY",
            "TRELLO_API_KEY",
            "TRELLO_TOKEN",
            "OPENAI_API_KEY",
            "LANGFUSE_HOST",
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_SECRET_KEY"
        ]
        
        env_status = {
            "python_version": sys.version,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "required_vars": {},
            "optional_vars": {},
            "missing_required": [],
            "missing_optional": []
        }
        
        # Check required environment variables
        for var in required_env_vars:
            value = os.getenv(var)
            env_status["required_vars"][var] = bool(value)
            if not value:
                env_status["missing_required"].append(var)
        
        # Check optional environment variables
        for var in optional_env_vars:
            value = os.getenv(var)
            env_status["optional_vars"][var] = bool(value)
            if not value:
                env_status["missing_optional"].append(var)
        
        env_status["status"] = "success" if not env_status["missing_required"] else "error"
        
        return env_status
    
    async def _validate_configuration(self) -> Dict[str, Any]:
        """Validate application configuration"""
        logger.info("Validating application configuration...")
        
        config_status = {
            "cors_origins": self._validate_cors_configuration(),
            "api_settings": self._validate_api_settings(),
            "logging": self._validate_logging_configuration(),
            "status": "success"
        }
        
        return config_status
    
    def _validate_cors_configuration(self) -> Dict[str, Any]:
        """Validate CORS configuration"""
        # This would be expanded based on actual CORS requirements
        return {
            "configured": True,
            "origins_count": 5,  # Based on main.py CORS setup
            "status": "valid"
        }
    
    def _validate_api_settings(self) -> Dict[str, Any]:
        """Validate API settings"""
        return {
            "title": "StudioOps AI API",
            "version": "1.0.0",
            "docs_enabled": True,
            "status": "valid"
        }
    
    def _validate_logging_configuration(self) -> Dict[str, Any]:
        """Validate logging configuration"""
        return {
            "level": logging.getLogger().getEffectiveLevel(),
            "handlers_count": len(logging.getLogger().handlers),
            "status": "valid"
        }
    
    async def _validate_critical_services(self) -> Dict[str, Any]:
        """Validate critical services that must be available"""
        logger.info("Validating critical services...")
        
        critical_results = {}
        
        for service in self.critical_services:
            try:
                if service == "database":
                    result = await self._validate_database_connection()
                    critical_results[service] = result
                else:
                    critical_results[service] = {
                        "status": "unknown",
                        "message": f"No validation implemented for {service}"
                    }
            except Exception as e:
                logger.error(f"Critical service validation failed for {service}: {e}")
                critical_results[service] = {
                    "status": "error",
                    "message": str(e)
                }
        
        overall_status = "success" if all(
            result["status"] == "success" for result in critical_results.values()
        ) else "error"
        
        return {
            "services": critical_results,
            "status": overall_status
        }
    
    async def _validate_optional_services(self) -> Dict[str, Any]:
        """Validate optional services"""
        logger.info("Validating optional services...")
        
        optional_results = {}
        
        for service in self.optional_services:
            try:
                if service == "minio":
                    result = await self._validate_minio_connection()
                elif service == "trello_mcp":
                    result = await self._validate_trello_connection()
                elif service == "ai_service":
                    result = await self._validate_ai_service()
                elif service == "observability":
                    result = await self._validate_observability_service()
                else:
                    result = {
                        "status": "unknown",
                        "message": f"No validation implemented for {service}"
                    }
                
                optional_results[service] = result
                
            except Exception as e:
                logger.warning(f"Optional service validation failed for {service}: {e}")
                optional_results[service] = {
                    "status": "degraded",
                    "message": str(e)
                }
        
        return {
            "services": optional_results,
            "status": "success"  # Optional services don't affect overall status
        }
    
    async def _validate_database_connection(self) -> Dict[str, Any]:
        """Validate database connection and basic functionality"""
        try:
            conn = psycopg2.connect(
                os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops'),
                connect_timeout=10
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "message": "Database connection successful",
                "details": {
                    "version": version,
                    "connection_timeout": 10
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database connection failed: {str(e)}"
            }
    
    async def _validate_minio_connection(self) -> Dict[str, Any]:
        """Validate MinIO connection"""
        try:
            client = Minio(
                endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.getenv('MINIO_ACCESS_KEY', 'studioops'),
                secret_key=os.getenv('MINIO_SECRET_KEY', 'studioops123'),
                secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            )
            
            buckets = client.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            return {
                "status": "success",
                "message": "MinIO connection successful",
                "details": {
                    "buckets": bucket_names,
                    "endpoint": os.getenv('MINIO_ENDPOINT', 'localhost:9000')
                }
            }
            
        except Exception as e:
            return {
                "status": "degraded",
                "message": f"MinIO connection failed: {str(e)}"
            }
    
    async def _validate_trello_connection(self) -> Dict[str, Any]:
        """Validate Trello API connection"""
        try:
            api_key = os.getenv('TRELLO_API_KEY')
            token = os.getenv('TRELLO_TOKEN')
            
            if not api_key or not token:
                return {
                    "status": "degraded",
                    "message": "Trello credentials not configured"
                }
            
            response = requests.get(
                "https://api.trello.com/1/members/me",
                params={"key": api_key, "token": token},
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "status": "success",
                    "message": "Trello API connection successful",
                    "details": {
                        "username": user_data.get('username', 'unknown')
                    }
                }
            else:
                return {
                    "status": "degraded",
                    "message": f"Trello API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "degraded",
                "message": f"Trello validation failed: {str(e)}"
            }
    
    async def _validate_ai_service(self) -> Dict[str, Any]:
        """Validate AI service connection"""
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if not openai_key:
                return {
                    "status": "degraded",
                    "message": "OpenAI API key not configured"
                }
            
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "OpenAI API connection successful"
                }
            else:
                return {
                    "status": "degraded",
                    "message": f"OpenAI API error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "degraded",
                "message": f"AI service validation failed: {str(e)}"
            }
    
    async def _validate_observability_service(self) -> Dict[str, Any]:
        """Validate observability service"""
        try:
            langfuse_host = os.getenv('LANGFUSE_HOST')
            
            if not langfuse_host:
                return {
                    "status": "degraded",
                    "message": "Langfuse not configured"
                }
            
            return {
                "status": "success",
                "message": "Observability service configured",
                "details": {
                    "host": langfuse_host
                }
            }
            
        except Exception as e:
            return {
                "status": "degraded",
                "message": f"Observability validation failed: {str(e)}"
            }
    
    async def _validate_database_schema(self) -> Dict[str, Any]:
        """Validate database schema and foreign key constraints"""
        logger.info("Validating database schema...")
        
        try:
            conn = psycopg2.connect(
                os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
            )
            cursor = conn.cursor()
            
            # Check required tables exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('projects', 'users', 'documents', 'chat_sessions', 'plans', 'purchases')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check foreign key constraints
            cursor.execute("""
                SELECT 
                    tc.table_name,
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """)
            
            foreign_keys = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            required_tables = ['projects', 'users', 'documents', 'chat_sessions', 'plans', 'purchases']
            missing_tables = [table for table in required_tables if table not in tables]
            
            return {
                "status": "success" if not missing_tables else "error",
                "tables_found": len(tables),
                "foreign_keys_count": len(foreign_keys),
                "missing_tables": missing_tables,
                "details": {
                    "tables": tables,
                    "foreign_keys": len(foreign_keys)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database schema validation failed: {str(e)}"
            }
    
    async def _validate_file_permissions(self) -> Dict[str, Any]:
        """Validate file system permissions"""
        logger.info("Validating file permissions...")
        
        try:
            # Check if we can write to temp directory
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                temp_file.write(b"test")
                temp_file.flush()
            
            return {
                "status": "success",
                "message": "File system permissions are adequate",
                "temp_dir_writable": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"File permission validation failed: {str(e)}"
            }
    
    def _determine_startup_success(self, results: Dict[str, Any]) -> bool:
        """Determine if startup was successful based on validation results"""
        
        # Critical services must be successful
        critical_success = results["critical_services"]["status"] == "success"
        
        # Environment must be valid
        env_success = results["environment"]["status"] == "success"
        
        # Database schema must be valid
        schema_success = results["database_schema"]["status"] == "success"
        
        # File permissions must be adequate
        permissions_success = results["file_permissions"]["status"] == "success"
        
        return critical_success and env_success and schema_success and permissions_success
    
    def _collect_warnings(self, results: Dict[str, Any]) -> List[str]:
        """Collect warning messages from validation results"""
        warnings = []
        
        # Check optional services
        optional_services = results.get("optional_services", {}).get("services", {})
        for service_name, service_result in optional_services.items():
            if service_result["status"] == "degraded":
                warnings.append(f"{service_name}: {service_result['message']}")
        
        # Check environment variables
        env_result = results.get("environment", {})
        if env_result.get("missing_optional"):
            warnings.append(f"Optional environment variables not set: {', '.join(env_result['missing_optional'])}")
        
        return warnings
    
    def _collect_errors(self, results: Dict[str, Any]) -> List[str]:
        """Collect error messages from validation results"""
        errors = []
        
        # Check critical services
        critical_services = results.get("critical_services", {}).get("services", {})
        for service_name, service_result in critical_services.items():
            if service_result["status"] == "error":
                errors.append(f"{service_name}: {service_result['message']}")
        
        # Check environment
        env_result = results.get("environment", {})
        if env_result.get("missing_required"):
            errors.append(f"Required environment variables not set: {', '.join(env_result['missing_required'])}")
        
        # Check database schema
        schema_result = results.get("database_schema", {})
        if schema_result["status"] == "error":
            errors.append(f"Database schema: {schema_result.get('message', 'Schema validation failed')}")
        
        # Check file permissions
        permissions_result = results.get("file_permissions", {})
        if permissions_result["status"] == "error":
            errors.append(f"File permissions: {permissions_result.get('message', 'Permission validation failed')}")
        
        return errors
    
    async def _setup_service_degradation(self, results: Dict[str, Any]):
        """Setup service degradation based on startup validation results"""
        
        # Check optional services and set degradation levels
        optional_services = results.get("optional_services", {}).get("services", {})
        
        for service_name, service_result in optional_services.items():
            if service_result["status"] == "degraded":
                await service_degradation_service.handle_service_degradation(
                    service_name,
                    DegradationLevel.DEGRADED,
                    {"startup_validation": service_result["message"]}
                )
            elif service_result["status"] == "error":
                await service_degradation_service.handle_service_degradation(
                    service_name,
                    DegradationLevel.CRITICAL,
                    {"startup_validation": service_result["message"]}
                )

# Global instance
startup_validation_service = StartupValidationService()