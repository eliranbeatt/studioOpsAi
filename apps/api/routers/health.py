"""
Health Monitoring Router for StudioOps AI System

Provides comprehensive health check endpoints for system monitoring,
diagnostics, and service dependency validation.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import logging
import os
from datetime import datetime

from services.health_monitoring_service import health_monitoring_service, ServiceStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
async def basic_health_check():
    """Basic health check endpoint for load balancers"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "studioops-api"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Comprehensive health check for all system components"""
    try:
        health_status = await health_monitoring_service.get_system_health()
        
        # Determine HTTP status code based on overall health
        if health_status["overall_status"] == ServiceStatus.UNHEALTHY.value:
            status_code = 503  # Service Unavailable
        elif health_status["overall_status"] == ServiceStatus.DEGRADED.value:
            status_code = 200  # OK but with warnings
        else:
            status_code = 200  # OK
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check system error: {str(e)}"
        )

@router.get("/services/{service_name}")
async def service_health_check(service_name: str):
    """Get health status for a specific service"""
    try:
        health_status = await health_monitoring_service.get_system_health()
        
        if service_name not in health_status["services"]:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service_name}' not found"
            )
        
        service_health = health_status["services"][service_name]
        
        return {
            "service": service_name,
            **service_health
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service health check failed for {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Service health check error: {str(e)}"
        )

@router.get("/dependencies")
async def service_dependencies():
    """Get service dependency validation and status"""
    try:
        dependencies = await health_monitoring_service.get_service_dependencies()
        
        # Count healthy vs unhealthy dependencies
        required_healthy = sum(
            1 for service in dependencies["required"].values()
            if service["status"] == ServiceStatus.HEALTHY.value
        )
        required_total = len(dependencies["required"])
        
        optional_healthy = sum(
            1 for service in dependencies["optional"].values()
            if service["status"] == ServiceStatus.HEALTHY.value
        )
        optional_total = len(dependencies["optional"])
        
        # Determine overall dependency health
        if required_healthy < required_total:
            overall_status = "critical"
        elif optional_healthy < optional_total:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "summary": {
                "required_healthy": f"{required_healthy}/{required_total}",
                "optional_healthy": f"{optional_healthy}/{optional_total}"
            },
            "dependencies": dependencies,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Dependency check error: {str(e)}"
        )

@router.get("/diagnostics")
async def system_diagnostics():
    """Comprehensive system diagnostics for troubleshooting"""
    try:
        # Get detailed health information
        health_status = await health_monitoring_service.get_system_health()
        dependencies = await health_monitoring_service.get_service_dependencies()
        
        # Environment information
        env_info = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": os.sys.version,
            "database_url_configured": bool(os.getenv("DATABASE_URL")),
            "minio_endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            "trello_configured": bool(os.getenv("TRELLO_API_KEY") and os.getenv("TRELLO_TOKEN")),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "langfuse_configured": bool(os.getenv("LANGFUSE_HOST"))
        }
        
        # Service status summary
        service_summary = {}
        for service_name, service_data in health_status["services"].items():
            service_summary[service_name] = {
                "status": service_data["status"],
                "response_time_ms": service_data.get("response_time_ms"),
                "last_check": service_data.get("timestamp")
            }
        
        # Identify issues and recommendations
        issues = []
        recommendations = []
        
        for service_name, service_data in health_status["services"].items():
            if service_data["status"] == ServiceStatus.UNHEALTHY.value:
                issues.append({
                    "service": service_name,
                    "issue": service_data["message"],
                    "severity": "high"
                })
                
                # Add specific recommendations
                if service_name == "database":
                    recommendations.append("Check database connection and ensure PostgreSQL is running")
                elif service_name == "minio":
                    recommendations.append("Verify MinIO server is running and credentials are correct")
                elif service_name == "trello_mcp":
                    recommendations.append("Check Trello API credentials and network connectivity")
                elif service_name == "ai_service":
                    recommendations.append("Verify OpenAI API key and check API quota")
            
            elif service_data["status"] == ServiceStatus.DEGRADED.value:
                issues.append({
                    "service": service_name,
                    "issue": service_data["message"],
                    "severity": "medium"
                })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": health_status["overall_status"],
            "system_info": health_status["system_info"],
            "environment": env_info,
            "service_summary": service_summary,
            "dependencies": dependencies,
            "issues": issues,
            "recommendations": recommendations,
            "health_check_duration_ms": health_status["response_time_ms"]
        }
        
    except Exception as e:
        logger.error(f"System diagnostics failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Diagnostics error: {str(e)}"
        )

@router.get("/readiness")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    try:
        health_status = await health_monitoring_service.get_system_health()
        
        # Check if critical services are healthy
        critical_services = ["database"]
        
        for service_name in critical_services:
            if service_name in health_status["services"]:
                service_status = health_status["services"][service_name]["status"]
                if service_status == ServiceStatus.UNHEALTHY.value:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Critical service '{service_name}' is unhealthy"
                    )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "critical_services_healthy": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check error: {str(e)}"
        )

@router.get("/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    try:
        # Simple check to ensure the application is responsive
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "studioops-api"
        }
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Liveness check error: {str(e)}"
        )

@router.get("/startup")
async def startup_check():
    """Kubernetes-style startup probe"""
    try:
        # Check if the application has completed initialization
        health_status = await health_monitoring_service.get_system_health()
        
        # Consider startup complete if we can get health status
        return {
            "status": "started",
            "timestamp": datetime.utcnow().isoformat(),
            "initialization_complete": True,
            "overall_health": health_status["overall_status"]
        }
        
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Startup check error: {str(e)}"
        )

@router.get("/metrics")
async def health_metrics():
    """Health metrics for monitoring systems"""
    try:
        health_status = await health_monitoring_service.get_system_health()
        
        # Convert to metrics format
        metrics = {
            "studioops_health_overall_status": 1 if health_status["overall_status"] == "healthy" else 0,
            "studioops_health_check_duration_ms": health_status["response_time_ms"],
            "studioops_health_services_total": len(health_status["services"]),
            "studioops_health_services_healthy": sum(
                1 for service in health_status["services"].values()
                if service["status"] == "healthy"
            ),
            "studioops_health_services_degraded": sum(
                1 for service in health_status["services"].values()
                if service["status"] == "degraded"
            ),
            "studioops_health_services_unhealthy": sum(
                1 for service in health_status["services"].values()
                if service["status"] == "unhealthy"
            )
        }
        
        # Add per-service metrics
        for service_name, service_data in health_status["services"].items():
            metrics[f"studioops_health_service_{service_name}_status"] = (
                1 if service_data["status"] == "healthy" else 0
            )
            if service_data.get("response_time_ms"):
                metrics[f"studioops_health_service_{service_name}_response_time_ms"] = service_data["response_time_ms"]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Health metrics failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Metrics error: {str(e)}"
        )

@router.post("/services/{service_name}/reset")
async def reset_service_cache(service_name: str):
    """Reset health check cache for a specific service"""
    try:
        # Clear cache for the specific service
        if hasattr(health_monitoring_service, 'service_checks'):
            if service_name in health_monitoring_service.service_checks:
                del health_monitoring_service.service_checks[service_name]
            if service_name in health_monitoring_service.last_check_time:
                del health_monitoring_service.last_check_time[service_name]
        
        return {
            "message": f"Cache reset for service '{service_name}'",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Service cache reset failed for {service_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache reset error: {str(e)}"
        )