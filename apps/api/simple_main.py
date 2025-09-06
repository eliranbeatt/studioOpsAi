from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Basic routers that should work
from routers import vendors, materials, chat, projects, plans, auth, estimation, vendor_prices, purchases, shipping_quotes, rate_cards

app = FastAPI(
    title="StudioOps AI API - Simple",
    description="Core API for StudioOps AI project management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002", "http://localhost:3009"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include basic routers
app.include_router(auth.router)
app.include_router(vendors.router)
app.include_router(materials.router)
app.include_router(chat.router)
app.include_router(projects.router)
app.include_router(plans.router)
app.include_router(vendor_prices.router)
app.include_router(purchases.router)
app.include_router(shipping_quotes.router)
app.include_router(rate_cards.router)

@app.get("/")
async def root():
    return {"message": "StudioOps AI API is running", "status": "ok"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "not_tested",
        "service": "studioops-api"
    }

@app.get("/api/health")
async def api_health():
    """API health endpoint"""
    return {"status": "ok", "service": "studioops-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)