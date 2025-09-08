"""
Service Degradation Service for StudioOps AI System

Implements graceful service degradation patterns to maintain system functionality
when external services are unavailable or degraded.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DegradationLevel(Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

class ServiceDegradationService:
    def __init__(self):
        self.service_states = {}
        self.degradation_handlers = {}
        self.fallback_responses = {}
        self.circuit_breakers = {}
        
        # Initialize default degradation handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default degradation handlers for core services"""
        
        # Database degradation handler
        self.register_degradation_handler(
            "database",
            self._database_degradation_handler
        )
        
        # Trello MCP degradation handler
        self.register_degradation_handler(
            "trello_mcp",
            self._trello_degradation_handler
        )
        
        # AI service degradation handler
        self.register_degradation_handler(
            "ai_service",
            self._ai_service_degradation_handler
        )
        
        # MinIO degradation handler
        self.register_degradation_handler(
            "minio",
            self._minio_degradation_handler
        )
    
    def register_degradation_handler(self, service_name: str, handler: Callable):
        """Register a degradation handler for a service"""
        self.degradation_handlers[service_name] = handler
        logger.info(f"Registered degradation handler for {service_name}")
    
    async def handle_service_degradation(self, service_name: str, 
                                       degradation_level: DegradationLevel,
                                       error_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle service degradation with appropriate fallback"""
        
        # Update service state
        self.service_states[service_name] = {
            "level": degradation_level,
            "timestamp": datetime.utcnow(),
            "error_context": error_context or {}
        }
        
        # Get degradation handler
        handler = self.degradation_handlers.get(service_name)
        
        if handler:
            try:
                return await handler(degradation_level, error_context)
            except Exception as e:
                logger.error(f"Degradation handler failed for {service_name}: {e}")
                return self._default_degradation_response(service_name, degradation_level)
        else:
            logger.warning(f"No degradation handler found for {service_name}")
            return self._default_degradation_response(service_name, degradation_level)
    
    def _default_degradation_response(self, service_name: str, 
                                    degradation_level: DegradationLevel) -> Dict[str, Any]:
        """Default degradation response when no specific handler exists"""
        return {
            "service": service_name,
            "status": "degraded",
            "level": degradation_level.value,
            "message": f"Service {service_name} is operating in degraded mode",
            "fallback_active": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _database_degradation_handler(self, level: DegradationLevel, 
                                          context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle database service degradation"""
        
        if level == DegradationLevel.CRITICAL or level == DegradationLevel.OFFLINE:
            # Database is critical - cannot provide meaningful fallback
            return {
                "service": "database",
                "status": "critical",
                "level": level.value,
                "message": "Database service is unavailable - system cannot function",
                "fallback_active": False,
                "actions_required": [
                    "Check database connection",
                    "Verify PostgreSQL is running",
                    "Check network connectivity",
                    "Review database logs"
                ]
            }
        
        elif level == DegradationLevel.DEGRADED:
            # Database is slow but functional
            return {
                "service": "database",
                "status": "degraded",
                "level": level.value,
                "message": "Database performance is degraded - some operations may be slower",
                "fallback_active": True,
                "recommendations": [
                    "Reduce query complexity",
                    "Implement query timeouts",
                    "Use cached data where possible"
                ]
            }
        
        return {
            "service": "database",
            "status": "normal",
            "level": level.value,
            "message": "Database service is operating normally"
        }
    
    async def _trello_degradation_handler(self, level: DegradationLevel, 
                                        context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle Trello MCP service degradation"""
        
        if level == DegradationLevel.CRITICAL or level == DegradationLevel.OFFLINE:
            # Trello is unavailable - use mock responses
            return {
                "service": "trello_mcp",
                "status": "degraded",
                "level": level.value,
                "message": "Trello API unavailable - using mock responses",
                "fallback_active": True,
                "fallback_mode": "mock",
                "mock_responses": {
                    "create_board": {
                        "id": "mock_board_id",
                        "name": "Mock Board",
                        "url": "https://trello.com/b/mock/mock-board",
                        "mock": True
                    },
                    "create_card": {
                        "id": "mock_card_id", 
                        "name": "Mock Card",
                        "url": "https://trello.com/c/mock/mock-card",
                        "mock": True
                    }
                }
            }
        
        elif level == DegradationLevel.DEGRADED:
            # Trello is slow but functional
            return {
                "service": "trello_mcp",
                "status": "degraded",
                "level": level.value,
                "message": "Trello API is slow - operations may take longer",
                "fallback_active": True,
                "recommendations": [
                    "Implement request timeouts",
                    "Add retry logic with backoff",
                    "Cache successful responses"
                ]
            }
        
        return {
            "service": "trello_mcp",
            "status": "normal",
            "level": level.value,
            "message": "Trello integration is operating normally"
        }
    
    async def _ai_service_degradation_handler(self, level: DegradationLevel, 
                                            context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle AI service degradation"""
        
        if level == DegradationLevel.CRITICAL or level == DegradationLevel.OFFLINE:
            # AI service unavailable - use enhanced mock responses
            return {
                "service": "ai_service",
                "status": "degraded",
                "level": level.value,
                "message": "AI service unavailable - using enhanced mock responses",
                "fallback_active": True,
                "fallback_mode": "enhanced_mock",
                "mock_capabilities": [
                    "Contextual project responses",
                    "Cost estimation templates",
                    "Planning suggestions",
                    "Material recommendations"
                ]
            }
        
        elif level == DegradationLevel.DEGRADED:
            # AI service is slow but functional
            return {
                "service": "ai_service",
                "status": "degraded",
                "level": level.value,
                "message": "AI service is slow - responses may be delayed",
                "fallback_active": True,
                "recommendations": [
                    "Reduce context size",
                    "Use shorter prompts",
                    "Implement response caching"
                ]
            }
        
        return {
            "service": "ai_service",
            "status": "normal",
            "level": level.value,
            "message": "AI service is operating normally"
        }
    
    async def _minio_degradation_handler(self, level: DegradationLevel, 
                                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """Handle MinIO service degradation"""
        
        if level == DegradationLevel.CRITICAL or level == DegradationLevel.OFFLINE:
            # MinIO unavailable - disable file uploads
            return {
                "service": "minio",
                "status": "degraded",
                "level": level.value,
                "message": "File storage unavailable - uploads disabled",
                "fallback_active": True,
                "fallback_mode": "uploads_disabled",
                "user_message": "File uploads are temporarily unavailable. Please try again later."
            }
        
        elif level == DegradationLevel.DEGRADED:
            # MinIO is slow but functional
            return {
                "service": "minio",
                "status": "degraded",
                "level": level.value,
                "message": "File storage is slow - uploads may take longer",
                "fallback_active": True,
                "recommendations": [
                    "Implement upload timeouts",
                    "Show progress indicators",
                    "Allow upload retry"
                ]
            }
        
        return {
            "service": "minio",
            "status": "normal",
            "level": level.value,
            "message": "File storage is operating normally"
        }
    
    def get_service_state(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get current degradation state for a service"""
        return self.service_states.get(service_name)
    
    def get_all_service_states(self) -> Dict[str, Any]:
        """Get degradation states for all services"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": self.service_states.copy()
        }
    
    def is_service_degraded(self, service_name: str) -> bool:
        """Check if a service is currently degraded"""
        state = self.service_states.get(service_name)
        if not state:
            return False
        
        return state["level"] != DegradationLevel.NORMAL
    
    def get_degradation_summary(self) -> Dict[str, Any]:
        """Get summary of system degradation status"""
        total_services = len(self.service_states)
        degraded_services = sum(
            1 for state in self.service_states.values()
            if state["level"] != DegradationLevel.NORMAL
        )
        
        critical_services = sum(
            1 for state in self.service_states.values()
            if state["level"] in [DegradationLevel.CRITICAL, DegradationLevel.OFFLINE]
        )
        
        # Determine overall system status
        if critical_services > 0:
            overall_status = "critical"
        elif degraded_services > 0:
            overall_status = "degraded"
        else:
            overall_status = "normal"
        
        return {
            "overall_status": overall_status,
            "total_services": total_services,
            "degraded_services": degraded_services,
            "critical_services": critical_services,
            "healthy_services": total_services - degraded_services,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def recover_service(self, service_name: str) -> Dict[str, Any]:
        """Attempt to recover a degraded service"""
        
        if service_name in self.service_states:
            # Remove degradation state
            del self.service_states[service_name]
            
            logger.info(f"Service {service_name} marked for recovery")
            
            return {
                "service": service_name,
                "status": "recovery_initiated",
                "message": f"Recovery initiated for {service_name}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "service": service_name,
            "status": "not_degraded",
            "message": f"Service {service_name} is not currently degraded",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_user_facing_status(self) -> Dict[str, Any]:
        """Get user-friendly system status for frontend display"""
        summary = self.get_degradation_summary()
        
        # Create user-friendly messages
        if summary["overall_status"] == "critical":
            status_message = "Some features are temporarily unavailable"
            status_color = "red"
        elif summary["overall_status"] == "degraded":
            status_message = "System is running with limited functionality"
            status_color = "yellow"
        else:
            status_message = "All systems operational"
            status_color = "green"
        
        # Get specific service impacts
        service_impacts = []
        for service_name, state in self.service_states.items():
            if state["level"] != DegradationLevel.NORMAL:
                impact = self._get_user_impact_message(service_name, state["level"])
                if impact:
                    service_impacts.append(impact)
        
        return {
            "status": summary["overall_status"],
            "message": status_message,
            "color": status_color,
            "service_impacts": service_impacts,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_user_impact_message(self, service_name: str, level: DegradationLevel) -> Optional[str]:
        """Get user-facing impact message for service degradation"""
        
        impact_messages = {
            "trello_mcp": {
                DegradationLevel.DEGRADED: "Trello export may be slower than usual",
                DegradationLevel.CRITICAL: "Trello export is temporarily unavailable",
                DegradationLevel.OFFLINE: "Trello export is temporarily unavailable"
            },
            "ai_service": {
                DegradationLevel.DEGRADED: "AI responses may be slower than usual",
                DegradationLevel.CRITICAL: "AI features are using simplified responses",
                DegradationLevel.OFFLINE: "AI features are using simplified responses"
            },
            "minio": {
                DegradationLevel.DEGRADED: "File uploads may be slower than usual",
                DegradationLevel.CRITICAL: "File uploads are temporarily unavailable",
                DegradationLevel.OFFLINE: "File uploads are temporarily unavailable"
            },
            "database": {
                DegradationLevel.DEGRADED: "Some operations may be slower than usual",
                DegradationLevel.CRITICAL: "System functionality is severely limited",
                DegradationLevel.OFFLINE: "System is temporarily unavailable"
            }
        }
        
        service_messages = impact_messages.get(service_name, {})
        return service_messages.get(level)

# Global instance
service_degradation_service = ServiceDegradationService()