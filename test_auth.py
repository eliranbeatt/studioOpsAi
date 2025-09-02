#!/usr/bin/env python3
"""
Test script for authentication system
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    """Test the authentication flow"""
    print("Testing authentication flow...")
    
    # Test registration
    print("1. Testing user registration...")
    register_data = {
        "email": "test@studioops.ai",
        "full_name": "Test User",
        "password": "Test123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ User registration successful")
            user_data = response.json()
            print(f"   User ID: {user_data['id']}")
        elif response.status_code == 400 and "already exists" in response.text:
            print("✓ User already exists (expected)")
        else:
            print(f"✗ Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Registration error: {e}")
        return False
    
    # Test login
    print("2. Testing user login...")
    login_data = {
        "email": "test@studioops.ai",
        "password": "Test123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✓ Login successful")
            token_data = response.json()
            access_token = token_data['access_token']
            print(f"   Access token: {access_token[:20]}...")
            
            # Test protected endpoint
            print("3. Testing protected endpoint...")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                print("✓ Protected endpoint access successful")
                print(f"   User email: {user_info['email']}")
                print(f"   User name: {user_info['full_name']}")
                return True
            else:
                print(f"✗ Protected endpoint failed: {response.status_code} - {response.text}")
                return False
        else:
            print(f"✗ Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False

def test_projects_auth():
    """Test projects endpoint with authentication"""
    print("\nTesting projects with authentication...")
    
    # First login to get token
    login_data = {"email": "test@studioops.ai", "password": "Test123!"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print("✗ Login failed for projects test")
            return False
        
        token_data = response.json()
        access_token = token_data['access_token']
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test getting projects
        response = requests.get(f"{BASE_URL}/projects", headers=headers)
        if response.status_code == 200:
            projects = response.json()
            print("✓ Projects endpoint accessible with auth")
            print(f"   Found {len(projects)} projects")
            return True
        else:
            print(f"✗ Projects endpoint failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Projects test error: {e}")
        return False

if __name__ == "__main__":
    print("Running authentication tests...")
    print("=" * 50)
    
    success = True
    success &= test_auth_flow()
    success &= test_projects_auth()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All authentication tests passed!")
        sys.exit(0)
    else:
        print("✗ Some authentication tests failed!")
        sys.exit(1)