from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
import psycopg2
import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from routers import vendors, materials, mem0, chat, projects, plans, auth, estimation, ingest, vendor_prices, purchases, shipping_quotes, rate_cards, health

# Conditionally import instructor router if dependencies are available
try:
    from routers import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError as e:
    print(f"Instructor router not available: {e}")
    INSTRUCTOR_AVAILABLE = False

# Conditionally import documents router if WeasyPrint is available
try:
    from routers import documents
    DOCUMENTS_AVAILABLE = True
except ImportError as e:
    print(f"Documents router not available: {e}")
    print("Continuing without PDF generation functionality")
    DOCUMENTS_AVAILABLE = False

from middleware.observability_middleware import ObservabilityMiddleware, ObservableAPIRoute
from middleware.error_middleware import GlobalErrorMiddleware, http_exception_handler, validation_exception_handler
from services.observability_service import observability_service
from services.startup_validation_service import startup_validation_service
from services.health_monitoring_service import health_monitoring_service
from services.service_degradation_service import service_degradation_service
from fastapi.exceptions import RequestValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting StudioOps AI API...")
    
    try:
        # Perform startup validation
        startup_results = await startup_validation_service.validate_system_startup()
        
        if startup_results["startup_successful"]:
            logger.info("System startup validation completed successfully")
        else:
            logger.warning("System startup validation completed with warnings/errors")
            for error in startup_results["errors"]:
                logger.error(f"Startup error: {error}")
            for warning in startup_results["warnings"]:
                logger.warning(f"Startup warning: {warning}")
        
        # Store startup results for health endpoints
        app.state.startup_results = startup_results
        
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        # Continue startup even if validation fails
        app.state.startup_results = {
            "startup_successful": False,
            "error": str(e)
        }
    
    yield
    
    # Shutdown
    logger.info("Shutting down StudioOps AI API...")
    # Cleanup code would go here

app = FastAPI(
    title="StudioOps AI API",
    description="Core API for StudioOps AI project management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3009",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware (should be first)
app.add_middleware(GlobalErrorMiddleware, include_stack_trace=True)  # Set to False in production

# Observability middleware
app.add_middleware(ObservabilityMiddleware)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Use custom route class for automatic observability
app.router.route_class = ObservableAPIRoute

# Include routers
app.include_router(health.router)  # Health monitoring first
app.include_router(auth.router)
app.include_router(vendors.router)
app.include_router(materials.router)
app.include_router(mem0.router)
app.include_router(chat.router)
app.include_router(projects.router)
app.include_router(plans.router)
if DOCUMENTS_AVAILABLE:
    app.include_router(documents.router)
app.include_router(vendor_prices.router)
app.include_router(purchases.router)
app.include_router(shipping_quotes.router)
app.include_router(rate_cards.router)
if INSTRUCTOR_AVAILABLE:
    app.include_router(instructor.router)
app.include_router(ingest.router)

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@app.get("/")
async def root():
    """Root endpoint with system status"""
    try:
        # Get basic system status
        degradation_summary = service_degradation_service.get_degradation_summary()
        user_status = service_degradation_service.get_user_facing_status()
        
        return {
            "message": "StudioOps AI API is running",
            "version": "1.0.0",
            "status": user_status["status"],
            "system_message": user_status["message"],
            "timestamp": user_status["timestamp"],
            "health_endpoint": "/api/health/detailed"
        }
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        return {
            "message": "StudioOps AI API is running",
            "version": "1.0.0",
            "status": "unknown",
            "error": "Status check failed"
        }

@app.get("/health")
async def legacy_health_check():
    """Legacy health check endpoint for backward compatibility"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            return {
                "status": "healthy",
                "database": "connected",
                "service": "studioops-api",
                "note": "Use /api/health/detailed for comprehensive health information"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
    
    return {"status": "unhealthy"}

@app.get("/api/observability/health")
async def observability_health():
    """Observability health check endpoint"""
    return {
        "status": "enabled" if observability_service.enabled else "disabled",
        "service": "langfuse",
        "details": {
            "initialized": observability_service.enabled,
            "public_key_configured": bool(os.getenv('LANGFUSE_PUBLIC_KEY')),
            "secret_key_configured": bool(os.getenv('LANGFUSE_SECRET_KEY')),
            "host": os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
        }
    }

@app.get("/api/system/status")
async def system_status():
    """User-friendly system status endpoint for frontend"""
    try:
        user_status = service_degradation_service.get_user_facing_status()
        startup_results = getattr(app.state, 'startup_results', {})
        
        return {
            **user_status,
            "startup_successful": startup_results.get("startup_successful", True),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"System status error: {e}")
        return {
            "status": "error",
            "message": "Unable to determine system status",
            "color": "red",
            "service_impacts": ["System status check failed"],
            "startup_successful": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
