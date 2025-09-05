from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from routers import vendors, materials, mem0, chat, projects, plans, auth, estimation, ingest, vendor_prices, purchases, shipping_quotes, rate_cards

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
    DOCUMENTS_AVAILABLE = False
from middleware.observability_middleware import ObservabilityMiddleware, ObservableAPIRoute
from services.observability_service import observability_service

app = FastAPI(
    title="StudioOps AI API",
    description="Core API for StudioOps AI project management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3009",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability middleware
app.add_middleware(ObservabilityMiddleware)

# Use custom route class for automatic observability
app.router.route_class = ObservableAPIRoute

# Include routers
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
    return {"message": "StudioOps AI API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
                "service": "studioops-api"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
    
    return {"status": "unhealthy"}

@app.get("/api/health")
async def api_health():
    """API health endpoint"""
    return {"status": "ok", "service": "studioops-api"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
