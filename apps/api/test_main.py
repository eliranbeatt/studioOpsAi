#!/usr/bin/env python3
"""
Simple test for the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "StudioOps AI API is running"

def test_api_health():
    """Test API health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "studioops-api"

if __name__ == "__main__":
    test_root()
    test_api_health()
    print("All tests passed!")