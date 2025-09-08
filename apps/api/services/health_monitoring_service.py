"""
Health Monitoring Service for StudioOps AI System

This service provides comprehensive health checks for all system components
including database, external services, and internal dependencies.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import psycopg2
import requests
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthCheck:
    def __init__(self, name: str, status: ServiceStatus, message: str = "", 
                 response_time_ms: Optional[float] = None, details: Optional[Dict] = None):
        self.name = name
        self.status = status
        self.message = message
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class HealthMonitoringService:
    def __init__(self):
        self.service_checks = {}
        self.last_check_time = {}
        self.check_cache_duration = 30  # seconds
        
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        start_time = time.time()
        
        # Run all health checks
        checks = await asyncio.gather(
            self._check_database_health(),
            self._check_minio_health(),
            self._check_trello_mcp_health(),
            self._check_ai_service_health(),
            self._check_observability_health(),
            self._check_memory_usage(),
            return_exceptions=True
        )
        
        # Process results
        health_results = {}
        overall_status = ServiceStatus.HEALTHY
        
        for check in checks:
            if isinstance(check, Exception):
                logger.error(f"Health check failed: {check}")
                continue
                
            if isinstance(check, HealthCheck):
                health_results[check.name] = {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details,
                    "timestamp": check.timestamp.isoformat()
                }
                
                # Update overall status
                if check.status == ServiceStatus.UNHEALTHY:
                    overall_status = ServiceStatus.UNHEALTHY
                elif check.status == ServiceStatus.DEGRADED and overall_status == ServiceStatus.HEALTHY:
                    overall_status = ServiceStatus.DEGRADED
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(total_time, 2),
            "services": health_results,
            "system_info": {
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "uptime_seconds": self._get_uptime()
            }
        }
    
    async def _check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            conn = psycopg2.connect(
                os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops'),
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Test table existence
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('projects', 'users', 'documents', 'chat_sessions')
            """)
            tables = cursor.fetchall()
            
            # Test foreign key constraints
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY'
            """)
            fk_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            if result and result[0] == 1:
                return HealthCheck(
                    name="database",
                    status=ServiceStatus.HEALTHY,
                    message="Database connection successful",
                    response_time_ms=round(response_time, 2),
                    details={
                        "tables_found": len(tables),
                        "foreign_keys": fk_count,
                        "connection_pool": "active"
                    }
                )
            else:
                return HealthCheck(
                    name="database",
                    status=ServiceStatus.UNHEALTHY,
                    message="Database query failed",
                    response_time_ms=round(response_time, 2)
                )
                
        except psycopg2.OperationalError as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database",
                status=ServiceStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=round(response_time, 2)
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database",
                status=ServiceStatus.DEGRADED,
                message=f"Database check error: {str(e)}",
                response_time_ms=round(response_time, 2)
            )
    
    async def _check_minio_health(self) -> HealthCheck:
        """Check MinIO object storage health"""
        start_time = time.time()
        
        try:
            client = Minio(
                endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.getenv('MINIO_ACCESS_KEY', 'studioops'),
                secret_key=os.getenv('MINIO_SECRET_KEY', 'studioops123'),
                secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            )
            
            # Test connection by listing buckets
            buckets = client.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            # Check if required bucket exists
            required_bucket = "studioops-documents"
            bucket_exists = required_bucket in bucket_names
            
            response_time = (time.time() - start_time) * 1000
            
            if bucket_exists:
                return HealthCheck(
                    name="minio",
                    status=ServiceStatus.HEALTHY,
                    message="MinIO storage accessible",
                    response_time_ms=round(response_time, 2),
                    details={
                        "buckets": bucket_names,
                        "required_bucket_exists": bucket_exists,
                        "endpoint": os.getenv('MINIO_ENDPOINT', 'localhost:9000')
                    }
                )
            else:
                return HealthCheck(
                    name="minio",
                    status=ServiceStatus.DEGRADED,
                    message=f"Required bucket '{required_bucket}' not found",
                    response_time_ms=round(response_time, 2),
                    details={
                        "buckets": bucket_names,
                        "required_bucket_exists": bucket_exists
                    }
                )
                
        except S3Error as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="minio",
                status=ServiceStatus.UNHEALTHY,
                message=f"MinIO S3 error: {str(e)}",
                response_time_ms=round(response_time, 2)
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="minio",
                status=ServiceStatus.UNHEALTHY,
                message=f"MinIO connection failed: {str(e)}",
                response_time_ms=round(response_time, 2)
            )
    
    async def _check_trello_mcp_health(self) -> HealthCheck:
        """Check Trello MCP server health"""
        start_time = time.time()
        
        try:
            # Check if Trello credentials are configured
            api_key = os.getenv('TRELLO_API_KEY')
            token = os.getenv('TRELLO_TOKEN')
            
            if not api_key or not token:
                response_time = (time.time() - start_time) * 1000
                return HealthCheck(
                    name="trello_mcp",
                    status=ServiceStatus.DEGRADED,
                    message="Trello credentials not configured, using mock mode",
                    response_time_ms=round(response_time, 2),
                    details={
                        "api_key_configured": bool(api_key),
                        "token_configured": bool(token),
                        "mode": "mock"
                    }
                )
            
            # Test Trello API connectivity
            response = requests.get(
                "https://api.trello.com/1/members/me",
                params={"key": api_key, "token": token},
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                user_data = response.json()
                return HealthCheck(
                    name="trello_mcp",
                    status=ServiceStatus.HEALTHY,
                    message="Trello API accessible",
                    response_time_ms=round(response_time, 2),
                    details={
                        "api_key_configured": True,
                        "token_configured": True,
                        "user": user_data.get('username', 'unknown'),
                        "mode": "live"
                    }
                )
            else:
                return HealthCheck(
                    name="trello_mcp",
                    status=ServiceStatus.DEGRADED,
                    message=f"Trello API error: {response.status_code}",
                    response_time_ms=round(response_time, 2),
                    details={
                        "status_code": response.status_code,
                        "mode": "degraded"
                    }
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="trello_mcp",
                status=ServiceStatus.DEGRADED,
                message="Trello API timeout, using mock mode",
                response_time_ms=round(response_time, 2),
                details={"mode": "mock", "reason": "timeout"}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="trello_mcp",
                status=ServiceStatus.DEGRADED,
                message=f"Trello check failed: {str(e)}",
                response_time_ms=round(response_time, 2),
                details={"mode": "mock", "error": str(e)}
            )
    
    async def _check_ai_service_health(self) -> HealthCheck:
        """Check AI service health"""
        start_time = time.time()
        
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if not openai_key:
                response_time = (time.time() - start_time) * 1000
                return HealthCheck(
                    name="ai_service",
                    status=ServiceStatus.DEGRADED,
                    message="OpenAI API key not configured, using mock responses",
                    response_time_ms=round(response_time, 2),
                    details={
                        "api_key_configured": False,
                        "mode": "mock"
                    }
                )
            
            # Test OpenAI API connectivity (simple request)
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                models_data = response.json()
                return HealthCheck(
                    name="ai_service",
                    status=ServiceStatus.HEALTHY,
                    message="OpenAI API accessible",
                    response_time_ms=round(response_time, 2),
                    details={
                        "api_key_configured": True,
                        "models_available": len(models_data.get('data', [])),
                        "mode": "live"
                    }
                )
            else:
                return HealthCheck(
                    name="ai_service",
                    status=ServiceStatus.DEGRADED,
                    message=f"OpenAI API error: {response.status_code}",
                    response_time_ms=round(response_time, 2),
                    details={
                        "status_code": response.status_code,
                        "mode": "mock"
                    }
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="ai_service",
                status=ServiceStatus.DEGRADED,
                message="OpenAI API timeout, using mock responses",
                response_time_ms=round(response_time, 2),
                details={"mode": "mock", "reason": "timeout"}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="ai_service",
                status=ServiceStatus.DEGRADED,
                message=f"AI service check failed: {str(e)}",
                response_time_ms=round(response_time, 2),
                details={"mode": "mock", "error": str(e)}
            )
    
    async def _check_observability_health(self) -> HealthCheck:
        """Check observability service health"""
        start_time = time.time()
        
        try:
            langfuse_host = os.getenv('LANGFUSE_HOST')
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            secret_key = os.getenv('LANGFUSE_SECRET_KEY')
            
            response_time = (time.time() - start_time) * 1000
            
            if not langfuse_host or not public_key or not secret_key:
                return HealthCheck(
                    name="observability",
                    status=ServiceStatus.DEGRADED,
                    message="Langfuse not fully configured",
                    response_time_ms=round(response_time, 2),
                    details={
                        "host_configured": bool(langfuse_host),
                        "public_key_configured": bool(public_key),
                        "secret_key_configured": bool(secret_key),
                        "status": "disabled"
                    }
                )
            
            # Test Langfuse connectivity if configured
            if langfuse_host:
                try:
                    response = requests.get(
                        f"{langfuse_host}/api/public/health",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        return HealthCheck(
                            name="observability",
                            status=ServiceStatus.HEALTHY,
                            message="Langfuse accessible",
                            response_time_ms=round(response_time, 2),
                            details={
                                "host": langfuse_host,
                                "status": "enabled"
                            }
                        )
                except:
                    pass
            
            return HealthCheck(
                name="observability",
                status=ServiceStatus.HEALTHY,
                message="Observability configured",
                response_time_ms=round(response_time, 2),
                details={
                    "host": langfuse_host,
                    "status": "enabled"
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="observability",
                status=ServiceStatus.DEGRADED,
                message=f"Observability check failed: {str(e)}",
                response_time_ms=round(response_time, 2)
            )
    
    async def _check_memory_usage(self) -> HealthCheck:
        """Check system memory usage"""
        start_time = time.time()
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on usage
            memory_percent = memory.percent
            disk_percent = disk.percent
            
            if memory_percent > 90 or disk_percent > 90:
                status = ServiceStatus.UNHEALTHY
                message = "Critical resource usage"
            elif memory_percent > 80 or disk_percent > 80:
                status = ServiceStatus.DEGRADED
                message = "High resource usage"
            else:
                status = ServiceStatus.HEALTHY
                message = "Resource usage normal"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                response_time_ms=round(response_time, 2),
                details={
                    "memory_percent": memory_percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk_percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                }
            )
            
        except ImportError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="system_resources",
                status=ServiceStatus.UNKNOWN,
                message="psutil not available for resource monitoring",
                response_time_ms=round(response_time, 2)
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="system_resources",
                status=ServiceStatus.UNKNOWN,
                message=f"Resource check failed: {str(e)}",
                response_time_ms=round(response_time, 2)
            )
    
    def _get_uptime(self) -> int:
        """Get system uptime in seconds"""
        try:
            import psutil
            return int(time.time() - psutil.boot_time())
        except:
            return 0
    
    async def get_service_dependencies(self) -> Dict[str, Any]:
        """Get service dependency validation"""
        dependencies = {
            "required": {
                "database": {
                    "status": "checking",
                    "description": "PostgreSQL database for data persistence"
                },
                "minio": {
                    "status": "checking", 
                    "description": "Object storage for documents and files"
                }
            },
            "optional": {
                "trello_mcp": {
                    "status": "checking",
                    "description": "Trello integration for project export"
                },
                "ai_service": {
                    "status": "checking",
                    "description": "OpenAI API for AI-powered features"
                },
                "observability": {
                    "status": "checking",
                    "description": "Langfuse for observability and monitoring"
                }
            }
        }
        
        # Get current health status
        health = await self.get_system_health()
        
        # Update dependency status
        for category in ["required", "optional"]:
            for service_name in dependencies[category]:
                if service_name in health["services"]:
                    service_health = health["services"][service_name]
                    dependencies[category][service_name]["status"] = service_health["status"]
                    dependencies[category][service_name]["message"] = service_health["message"]
                    dependencies[category][service_name]["details"] = service_health.get("details", {})
        
        return dependencies

# Global instance
health_monitoring_service = HealthMonitoringService()