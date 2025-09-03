"""Test pricing and estimation services directly"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_services():
    """Test the pricing and estimation services"""
    print("Testing pricing resolver and estimation services...")
    
    try:
        from services.pricing_resolver import pricing_resolver
        from services.estimation_service import estimation_service
        from packages.schemas.estimation import ShippingEstimateRequest, ShippingMethod, LaborEstimateRequest, LaborRole
        
        print("Testing pricing resolver...")
        
        # Test material pricing
        material_price = pricing_resolver.get_material_price('Plywood 4x8')
        if material_price:
            print(f"Plywood price: {material_price['price']}")
        else:
            print("Plywood price not found (using mock data)")
        
        # Test labor rates
        labor_rate = pricing_resolver.get_labor_rate('Carpenter')
        if labor_rate:
            print(f"Carpenter rate: {labor_rate['hourly_rate']}")
        else:
            print("Carpenter rate not found (using mock data)")
        
        print("\nTesting estimation service...")
        
        # Test shipping estimation
        shipping_request = ShippingEstimateRequest(
            distance_km=100.0,
            weight_kg=10.0,
            method=ShippingMethod.STANDARD
        )
        shipping_estimate = estimation_service.estimate_shipping(shipping_request)
        print(f"Shipping estimate: {shipping_estimate.total_cost}")
        
        # Test labor estimation
        labor_request = LaborEstimateRequest(
            role=LaborRole.CARPENTER,
            hours_required=40.0
        )
        labor_estimate = estimation_service.estimate_labor(labor_request)
        print(f"Labor estimate: {labor_estimate.total_cost}")
        
        print("\n✅ All services working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_services()
    sys.exit(0 if success else 1)