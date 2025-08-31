#!/usr/bin/env python3
"""Test script for plan generation functionality"""

import sys
import os

# Add the apps/api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from apps.api.routers.chat import generate_plan_skeleton

async def test_plan_generation():
    """Test the plan generation with different project types"""
    
    print("Testing plan generation...")
    
    # Test 1: Cabinet project
    cabinet_request = {
        'project_name': 'Custom Cabinet',
        'project_description': 'Build a custom kitchen cabinet with drawers and shelves'
    }
    
    print("\n1. Cabinet Project:")
    cabinet_plan = await generate_plan_skeleton(cabinet_request)
    print(f"   Project: {cabinet_plan['project_name']}")
    print(f"   Total: NIS {cabinet_plan['total']}")
    print(f"   Items: {cabinet_plan['metadata']['items_count']}")
    print(f"   Materials: {cabinet_plan['metadata']['materials_count']}")
    print(f"   Labor: {cabinet_plan['metadata']['labor_count']}")
    
    # Test 2: Painting project
    painting_request = {
        'project_name': 'Room Painting',
        'project_description': 'Paint living room walls and ceiling'
    }
    
    print("\n2. Painting Project:")
    painting_plan = await generate_plan_skeleton(painting_request)
    print(f"   Project: {painting_plan['project_name']}")
    print(f"   Total: NIS {painting_plan['total']}")
    print(f"   Items: {painting_plan['metadata']['items_count']}")
    print(f"   Materials: {painting_plan['metadata']['materials_count']}")
    print(f"   Labor: {painting_plan['metadata']['labor_count']}")
    
    # Test 3: Complex project
    complex_request = {
        'project_name': 'Office Renovation',
        'project_description': 'Complete office renovation with electrical work, painting, and custom furniture. This is a large complex project.'
    }
    
    print("\n3. Complex Project:")
    complex_plan = await generate_plan_skeleton(complex_request)
    print(f"   Project: {complex_plan['project_name']}")
    print(f"   Total: NIS {complex_plan['total']}")
    print(f"   Items: {complex_plan['metadata']['items_count']}")
    print(f"   Materials: {complex_plan['metadata']['materials_count']}")
    print(f"   Labor: {complex_plan['metadata']['labor_count']}")
    
    print("\nPlan generation test completed successfully!")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_plan_generation())