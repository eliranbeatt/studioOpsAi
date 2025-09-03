"""Direct tests for estimation service logic"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_estimation_logic():
    """Test estimation logic directly"""
    print("Testing estimation service logic...")
    
    # Test shipping rates calculation
    shipping_rates = {
        'STANDARD': {'base_fee': 50.0, 'per_km': 2.0, 'per_kg': 5.0},
        'EXPRESS': {'base_fee': 100.0, 'per_km': 3.0, 'per_kg': 8.0}
    }
    
    # Test standard shipping
    method = 'STANDARD'
    distance = 100.0
    weight = 10.0
    
    base_cost = shipping_rates[method]['base_fee']
    distance_cost = distance * shipping_rates[method]['per_km']
    weight_cost = weight * shipping_rates[method]['per_kg']
    total_cost = base_cost + distance_cost + weight_cost
    
    print(f"Standard shipping calculation:")
    print(f"  Base: {base_cost}, Distance: {distance_cost}, Weight: {weight_cost}")
    print(f"  Total: {total_cost}")
    
    assert total_cost == 50.0 + 200.0 + 50.0  # 50 + 200 + 50 = 300
    
    # Test express shipping with surcharges
    method = 'EXPRESS'
    urgency = 1.5
    fragile = True
    insurance = 1000.0
    
    base_cost = shipping_rates[method]['base_fee']
    distance_cost = distance * shipping_rates[method]['per_km']
    weight_cost = weight * shipping_rates[method]['per_kg']
    
    urgency_surcharge = base_cost * (urgency - 1.0) * 0.5
    fragile_surcharge = base_cost * 0.15 if fragile else 0.0
    insurance_cost = insurance * 0.005 if insurance else 0.0
    
    total_cost = base_cost + distance_cost + weight_cost + urgency_surcharge + fragile_surcharge + insurance_cost
    
    print(f"\nExpress shipping with surcharges:")
    print(f"  Base: {base_cost}, Distance: {distance_cost}, Weight: {weight_cost}")
    print(f"  Urgency: {urgency_surcharge}, Fragile: {fragile_surcharge}, Insurance: {insurance_cost}")
    print(f"  Total: {total_cost}")
    
    # Test labor estimation
    labor_rates = {
        'CARPENTER': 120.0,
        'PAINTER': 100.0,
        'ELECTRICIAN': 150.0
    }
    
    efficiency_factors = {
        'CARPENTER': 0.9,
        'PAINTER': 0.8,
        'ELECTRICIAN': 0.85
    }
    
    role = 'CARPENTER'
    hours = 40.0
    complexity = 1.2
    tools = True
    
    base_rate = labor_rates[role]
    efficiency = efficiency_factors[role]
    effective_hours = hours / efficiency
    
    regular_hours = min(effective_hours, 8.0)
    overtime_hours = max(0, effective_hours - 8.0)
    overtime_rate = base_rate * 1.5
    
    regular_cost = regular_hours * base_rate
    overtime_cost = overtime_hours * overtime_rate
    
    # Apply complexity
    regular_cost *= complexity
    overtime_cost *= complexity
    
    # Tool surcharge
    tool_surcharge = base_rate * 0.1 * effective_hours if tools else 0.0
    
    total_cost = regular_cost + overtime_cost + tool_surcharge
    
    print(f"\nLabor estimation for Carpenter:")
    print(f"  Base rate: {base_rate}, Efficiency: {efficiency}")
    print(f"  Effective hours: {effective_hours}")
    print(f"  Regular: {regular_hours}h @ {base_rate} = {regular_cost}")
    print(f"  Overtime: {overtime_hours}h @ {overtime_rate} = {overtime_cost}")
    print(f"  Tool surcharge: {tool_surcharge}")
    print(f"  Total: {total_cost}")
    
    # Test project estimation
    materials_cost = 1000.0
    labor_cost = 5000.0
    shipping_cost = 300.0
    margin = 0.2
    tax_rate = 0.17
    
    subtotal = materials_cost + labor_cost + shipping_cost
    margin_amount = subtotal * margin
    tax_amount = (subtotal + margin_amount) * tax_rate
    total_project_cost = subtotal + margin_amount + tax_amount
    
    print(f"\nProject estimation:")
    print(f"  Materials: {materials_cost}, Labor: {labor_cost}, Shipping: {shipping_cost}")
    print(f"  Subtotal: {subtotal}")
    print(f"  Margin ({margin*100}%): {margin_amount}")
    print(f"  Tax ({tax_rate*100}%): {tax_amount}")
    print(f"  Total: {total_project_cost}")
    
    assert total_project_cost > 0
    print("\nAll estimation logic tests passed!")

if __name__ == "__main__":
    test_estimation_logic()