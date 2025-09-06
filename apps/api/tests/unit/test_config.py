"""Test configuration and constants"""

import os
from pathlib import Path

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)

# Test database configuration
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/studioops_test")

# Test API configuration
TEST_API_URL = "http://localhost:8000"
TEST_API_PREFIX = "/api/v1"

# Test timeout configuration
TEST_TIMEOUT = 30  # seconds

# Test file paths
TEST_PDF_OUTPUT_DIR = TEST_DATA_DIR / "pdf_output"
TEST_PDF_OUTPUT_DIR.mkdir(exist_ok=True)

TEST_UPLOAD_DIR = TEST_DATA_DIR / "uploads"
TEST_UPLOAD_DIR.mkdir(exist_ok=True)

# Test user data
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
}

# Test project data
TEST_PROJECT = {
    "name": "Test Project",
    "description": "Test project description",
    "status": "planned",
    "budget": 10000.0,
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59"
}

# Test vendor data
TEST_VENDOR = {
    "name": "Test Vendor",
    "contact": "vendor@example.com",
    "rating": 4.5,
    "specialty": "construction"
}

# Test material data
TEST_MATERIAL = {
    "name": "Test Material",
    "description": "Test material description",
    "unit": "kg",
    "unit_price": 25.99,
    "category": "building"
}

# Test plan data
TEST_PLAN = {
    "project_name": "Test Project Plan",
    "items": [
        {
            "category": "materials",
            "title": "Test Material Item",
            "description": "Test material description",
            "quantity": 10.0,
            "unit": "unit",
            "unit_price": 100.0,
            "subtotal": 1000.0
        },
        {
            "category": "labor",
            "title": "Test Labor Item",
            "description": "Test labor description",
            "quantity": 5.0,
            "unit": "hour",
            "unit_price": 50.0,
            "subtotal": 250.0
        }
    ],
    "total": 1250.0,
    "margin_target": 0.2,
    "currency": "USD"
}