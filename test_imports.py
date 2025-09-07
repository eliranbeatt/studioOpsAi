#!/usr/bin/env python3
"""Test imports to debug the 500 errors"""

import sys
import os

# Add the apps/api directory to the path
sys.path.insert(0, os.path.join(os.getcwd(), 'apps', 'api'))

try:
    print("Testing imports...")
    
    # Test database import
    from database import get_db
    print("✅ Database import successful")
    
    # Test models import
    from models import Vendor as VendorModel
    print("✅ Models import successful")
    
    # Test schema imports
    from packages.schemas.models import Vendor, VendorCreate, VendorUpdate
    print("✅ Schema imports successful")
    
    # Test creating a vendor model instance
    vendor_data = VendorCreate(name="Test Vendor")
    print(f"✅ VendorCreate instance: {vendor_data}")
    
    print("\n🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()