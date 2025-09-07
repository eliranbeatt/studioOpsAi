#!/usr/bin/env python3
"""
Test SQLAlchemy models directly to debug the 500 errors
"""

import sys
import os

# Add the apps/api directory to the path
sys.path.insert(0, os.path.join(os.getcwd(), 'apps', 'api'))

from database import SessionLocal
from models import Vendor as VendorModel, Material as MaterialModel, Project as ProjectModel

def test_vendor_query():
    """Test querying vendors directly"""
    print("Testing Vendor query...")
    
    db = SessionLocal()
    try:
        vendors = db.query(VendorModel).order_by(VendorModel.name).all()
        print(f"✅ Found {len(vendors)} vendors")
        
        if vendors:
            vendor = vendors[0]
            print(f"First vendor: {vendor.name} (ID: {vendor.id}, type: {type(vendor.id)})")
            print(f"Contact: {vendor.contact} (type: {type(vendor.contact)})")
            print(f"Rating: {vendor.rating} (type: {type(vendor.rating)})")
            
            # Try to serialize to dict
            try:
                vendor_dict = {
                    "id": str(vendor.id),
                    "name": vendor.name,
                    "contact": vendor.contact,
                    "url": vendor.url,
                    "rating": vendor.rating,
                    "notes": vendor.notes,
                    "created_at": vendor.created_at,
                    "updated_at": vendor.updated_at
                }
                print("✅ Vendor serialization successful")
                return True
            except Exception as e:
                print(f"❌ Vendor serialization failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
    except Exception as e:
        print(f"❌ Vendor query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_material_query():
    """Test querying materials directly"""
    print("\nTesting Material query...")
    
    db = SessionLocal()
    try:
        materials = db.query(MaterialModel).order_by(MaterialModel.name).all()
        print(f"✅ Found {len(materials)} materials")
        
        if materials:
            material = materials[0]
            print(f"First material: {material.name} (ID: {material.id}, type: {type(material.id)})")
            print(f"Unit: {material.unit}")
            print(f"Waste %: {material.typical_waste_pct} (type: {type(material.typical_waste_pct)})")
            
            # Try to serialize to dict
            try:
                material_dict = {
                    "id": str(material.id),
                    "name": material.name,
                    "spec": material.spec,
                    "unit": material.unit,
                    "category": material.category,
                    "typical_waste_pct": float(material.typical_waste_pct) if material.typical_waste_pct else 0.0,
                    "notes": material.notes,
                    "created_at": material.created_at,
                    "updated_at": material.updated_at
                }
                print("✅ Material serialization successful")
                return True
            except Exception as e:
                print(f"❌ Material serialization failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
    except Exception as e:
        print(f"❌ Material query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_project_query():
    """Test querying projects directly"""
    print("\nTesting Project query...")
    
    db = SessionLocal()
    try:
        projects = db.query(ProjectModel).order_by(ProjectModel.created_at.desc()).all()
        print(f"✅ Found {len(projects)} projects")
        
        if projects:
            project = projects[0]
            print(f"First project: {project.name} (ID: {project.id}, type: {type(project.id)})")
            print(f"Budget planned: {project.budget_planned} (type: {type(project.budget_planned)})")
            
            # Try to serialize to dict
            try:
                project_dict = {
                    "id": str(project.id),
                    "name": project.name,
                    "client_name": project.client_name,
                    "status": project.status,
                    "start_date": project.start_date,
                    "due_date": project.due_date,
                    "budget_planned": float(project.budget_planned) if project.budget_planned else None,
                    "budget_actual": float(project.budget_actual) if project.budget_actual else None,
                    "board_id": project.board_id,
                    "created_at": project.created_at,
                    "updated_at": project.updated_at
                }
                print("✅ Project serialization successful")
                return True
            except Exception as e:
                print(f"❌ Project serialization failed: {e}")
                import traceback
                traceback.print_exc()
                return False
        
    except Exception as e:
        print(f"❌ Project query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    print("🔍 SQLAlchemy Direct Testing")
    print("=" * 40)
    
    vendor_ok = test_vendor_query()
    material_ok = test_material_query()
    project_ok = test_project_query()
    
    print("\n" + "=" * 40)
    print("📊 Results:")
    print(f"Vendor: {'✅' if vendor_ok else '❌'}")
    print(f"Material: {'✅' if material_ok else '❌'}")
    print(f"Project: {'✅' if project_ok else '❌'}")

if __name__ == "__main__":
    main()