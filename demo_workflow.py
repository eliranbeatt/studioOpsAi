#!/usr/bin/env python3
"""
Demo workflow for StudioOps AI system
This demonstrates the complete workflow from chat to plan generation to plan editing
"""

import json
import time
from datetime import datetime, timezone

# Mock data that matches what would come from the API
mock_prices = {
    'Plywood 4x8': {
        'material_id': 'mock-plywood-id',
        'material_name': 'Plywood 4x8',
        'unit': 'sheet',
        'price': 45.99,
        'confidence': 0.9,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Hardware Store',
        'vendor_rating': 4,
        'sku': 'PLY-001',
        'is_quote': False
    },
    '2x4 Lumber': {
        'material_id': 'mock-lumber-id',
        'material_name': '2x4 Lumber',
        'unit': 'piece',
        'price': 8.99,
        'confidence': 0.9,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Lumber Yard',
        'vendor_rating': 5,
        'sku': 'LUM-001',
        'is_quote': False
    }
}

mock_rates = {
    'Carpenter': {'role': 'Carpenter', 'hourly_rate': 120.0, 'efficiency': 0.9}
}

def simulate_chat_response(message):
    """Simulate AI chat response"""
    responses = {
        "hello": "Hello! How can I help you with your project today?",
        "project": "I'd be happy to help with planning. Describe your project and I'll give you recommendations.",
        "cabinet": "Excellent! For cabinet construction I recommend:\n- Wood panels (plywood)\n- 2x4 lumber\n- Screws\n- Carpenter work\n\nI can create a detailed work plan with pricing for you.",
        "default": "Great! I'm here to help with project management."
    }
    
    message_lower = message.lower()
    
    if "hello" in message_lower:
        return responses["hello"]
    elif "project" in message_lower:
        return responses["project"]
    elif "cabinet" in message_lower:
        return responses["cabinet"]
    else:
        return responses["default"]

def generate_plan_from_chat(chat_message):
    """Generate a plan based on chat context"""
    print(f"Analyzing chat message: {chat_message}")
    
    # Context-aware material selection
    materials_to_include = []
    if 'cabinet' in chat_message.lower():
        materials_to_include = ['Plywood 4x8', '2x4 Lumber']
        labor_roles = ['Carpenter']
        project_type = "Cabinet Construction"
    else:
        materials_to_include = ['Plywood 4x8', '2x4 Lumber']
        labor_roles = ['Carpenter']
        project_type = "General Construction"
    
    print(f"Selected materials: {materials_to_include}")
    print(f"Selected labor roles: {labor_roles}")
    
    # Build the plan
    items = []
    total = 0.0
    
    # Add materials
    for material_name in materials_to_include:
        price_data = mock_prices.get(material_name)
        if price_data:
            # Estimate quantity based on project type
            quantity = 8.0 if 'cabinet' in chat_message.lower() else 4.0
            subtotal = quantity * price_data['price']
            
            items.append({
                "category": "materials",
                "title": price_data['material_name'],
                "description": f"{material_name} from {price_data['vendor_name']}",
                "quantity": quantity,
                "unit": price_data['unit'],
                "unit_price": price_data['price'],
                "unit_price_source": {
                    "vendor": price_data['vendor_name'],
                    "confidence": price_data['confidence'],
                    "fetched_at": price_data['fetched_at'].isoformat()
                },
                "subtotal": round(subtotal, 2)
            })
            total += subtotal
    
    # Add labor
    for role in labor_roles:
        labor_data = mock_rates.get(role)
        if labor_data:
            # Estimate hours based on project complexity
            hours = 16.0 if 'cabinet' in chat_message.lower() else 8.0
            subtotal = hours * labor_data['hourly_rate']
            
            items.append({
                "category": "labor",
                "title": f"{role} work",
                "description": f"{role} services for the project",
                "quantity": hours,
                "unit": "hour",
                "unit_price": labor_data['hourly_rate'],
                "labor_role": role,
                "labor_hours": hours,
                "subtotal": round(subtotal, 2)
            })
            total += subtotal
    
    # Add logistics
    shipping_cost = 250.0
    items.append({
        "category": "logistics",
        "title": "Shipping & Delivery",
        "description": "Material delivery and logistics",
        "quantity": 1,
        "unit": "delivery",
        "unit_price": shipping_cost,
        "subtotal": round(shipping_cost, 2)
    })
    total += shipping_cost
    
    plan = {
        "project_id": f"proj-{int(time.time())}",
        "project_name": "Custom Project from Chat",
        "items": items,
        "total": round(total, 2),
        "margin_target": 0.25,
        "currency": "NIS",
        "metadata": {
            "generated_at": time.time(),
            "items_count": len(items),
            "project_type": project_type,
            "source": "chat_context"
        }
    }
    
    return plan

def demonstrate_plan_editing(plan):
    """Demonstrate plan editing capabilities"""
    print("\nPLAN EDITOR DEMONSTRATION")
    print("=" * 50)
    
    # Show original plan
    print("\nOriginal Plan:")
    print(f"Project: {plan['project_name']}")
    print(f"Total: {plan['total']} {plan['currency']}")
    print(f"Items: {len(plan['items'])}")
    
    # Simulate editing a quantity
    print("\nSimulating quantity edit...")
    original_quantity = plan['items'][0]['quantity']
    new_quantity = original_quantity + 2
    plan['items'][0]['quantity'] = new_quantity
    plan['items'][0]['subtotal'] = new_quantity * plan['items'][0]['unit_price']
    
    # Recalculate total
    plan['total'] = sum(item['subtotal'] for item in plan['items'])
    
    print(f"Changed quantity from {original_quantity} to {new_quantity}")
    print(f"New subtotal: {plan['items'][0]['subtotal']}")
    print(f"New total: {plan['total']}")
    
    # Simulate adding a new item
    print("\nSimulating adding new item...")
    new_item = {
        "category": "materials",
        "title": "Screws",
        "description": "Construction screws",
        "quantity": 2,
        "unit": "box",
        "unit_price": 12.99,
        "subtotal": 25.98
    }
    plan['items'].append(new_item)
    plan['total'] = sum(item['subtotal'] for item in plan['items'])
    
    print(f"Added: {new_item['title']}")
    print(f"New total: {plan['total']}")
    
    return plan

def main():
    """Main demo workflow"""
    print("STUDIO OPS AI - COMPLETE WORKFLOW DEMO")
    print("=" * 50)
    
    # Step 1: Chat interaction
    print("\n1. CHAT INTERACTION")
    print("-" * 30)
    
    chat_message = "I want to build a cabinet for my kitchen"
    print(f"User: {chat_message}")
    
    ai_response = simulate_chat_response(chat_message)
    print(f"AI: {ai_response}")
    
    # Step 2: Plan generation
    print("\n2. PLAN GENERATION")
    print("-" * 30)
    
    plan = generate_plan_from_chat(chat_message)
    print(f"Plan generated successfully!")
    print(f"   Project ID: {plan['project_id']}")
    print(f"   Total: {plan['total']} {plan['currency']}")
    print(f"   Items: {len(plan['items'])}")
    
    # Step 3: Plan editing demonstration
    print("\n3. PLAN EDITING")
    print("-" * 30)
    
    edited_plan = demonstrate_plan_editing(plan)
    
    # Step 4: Final result
    print("\n4. FINAL RESULT")
    print("-" * 30)
    
    print(f"Final Project: {edited_plan['project_name']}")
    print(f"Final Total: {edited_plan['total']} {edited_plan['currency']}")
    print(f"Final Items: {len(edited_plan['items'])}")
    
    print("\nItem breakdown:")
    for i, item in enumerate(edited_plan['items'], 1):
        print(f"   {i}. {item['title']}: {item['quantity']} {item['unit']} × {item['unit_price']} = {item['subtotal']}")
    
    # Save demo result
    with open('demo_plan_result.json', 'w', encoding='utf-8') as f:
        json.dump(edited_plan, f, indent=2, ensure_ascii=False)
    
    print(f"\nDemo plan saved to: demo_plan_result.json")
    print("\nWORKFLOW COMPLETED SUCCESSFULLY!")
    print("\nThe system demonstrates:")
    print("  - Chat-based project initiation")
    print("  - Context-aware material selection") 
    print("  - Automated pricing from vendor database")
    print("  - Plan generation with real-time calculations")
    print("  - Spreadsheet-like editing interface")
    print("  - Automatic total recalculation")

if __name__ == "__main__":
    main()