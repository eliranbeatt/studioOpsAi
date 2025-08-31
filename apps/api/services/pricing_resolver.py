from typing import Optional, Dict, Any
import os
from datetime import datetime, timezone

try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

class PricingResolver:
    """Service to resolve prices from vendor database"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
    
    def get_connection(self):
        """Get database connection"""
        if not HAS_POSTGRES:
            return None
        return psycopg2.connect(self.db_url)
    
    def get_material_price(self, material_name: str, vendor_priority: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get best price for a material with vendor priority"""
        # Mock data for testing - matches seed data
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
            },
            'Screws': {
                'material_id': 'mock-screws-id',
                'material_name': 'Screws',
                'unit': 'box',
                'price': 12.99,
                'confidence': 0.85,
                'fetched_at': datetime.now(timezone.utc),
                'vendor_name': 'Hardware Store',
                'vendor_rating': 4,
                'sku': 'SCR-001',
                'is_quote': False
            },
            'Paint': {
                'material_id': 'mock-paint-id',
                'material_name': 'Paint',
                'unit': 'gallon',
                'price': 85.00,
                'confidence': 0.8,
                'fetched_at': datetime.now(timezone.utc),
                'vendor_name': 'Paint Store',
                'vendor_rating': 4,
                'sku': 'PAINT-001',
                'is_quote': False
            },
            'Nails': {
                'material_id': 'mock-nails-id',
                'material_name': 'Nails',
                'unit': 'lb',
                'price': 25.00,
                'confidence': 0.75,
                'fetched_at': datetime.now(timezone.utc),
                'vendor_name': 'Hardware Store',
                'vendor_rating': 4,
                'sku': 'NAILS-001',
                'is_quote': False
            }
        }
        
        # Return mock data if database not available
        if not HAS_POSTGRES:
            return mock_prices.get(material_name)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # First try to find the material
                    cursor.execute(
                        "SELECT id, name, unit FROM materials WHERE name ILIKE %s",
                        (f'%{material_name}%',)
                    )
                    material = cursor.fetchone()
                    
                    if not material:
                        return None
                    
                    material_id, material_name, unit = material
                    
                    # Get best price (highest confidence, most recent)
                    query = """
                        SELECT vp.price_nis, vp.confidence, vp.fetched_at, 
                               v.name as vendor_name, v.rating,
                               vp.sku, vp.is_quote
                        FROM vendor_prices vp
                        JOIN vendors v ON vp.vendor_id = v.id
                        WHERE vp.material_id = %s
                        ORDER BY vp.confidence DESC, vp.fetched_at DESC
                        LIMIT 1
                    """
                    
                    cursor.execute(query, (material_id,))
                    price_data = cursor.fetchone()
                    
                    if price_data:
                        return {
                            'material_id': material_id,
                            'material_name': material_name,
                            'unit': unit,
                            'price': float(price_data[0]),
                            'confidence': float(price_data[1]),
                            'fetched_at': price_data[2],
                            'vendor_name': price_data[3],
                            'vendor_rating': price_data[4],
                            'sku': price_data[5],
                            'is_quote': price_data[6]
                        }
                    
                    return None
                    
        except Exception as e:
            print(f"Error getting material price: {e}")
            # Fall back to mock data
            return mock_prices.get(material_name)
    
    def get_labor_rate(self, role: str) -> Optional[Dict[str, Any]]:
        """Get labor rate for a specific role"""
        # Mock data for testing
        mock_rates = {
            'Carpenter': {'role': 'Carpenter', 'hourly_rate': 120.0, 'efficiency': 0.9},
            'Painter': {'role': 'Painter', 'hourly_rate': 100.0, 'efficiency': 0.8},
            'Electrician': {'role': 'Electrician', 'hourly_rate': 150.0, 'efficiency': 0.85},
            'Laborer': {'role': 'Laborer', 'hourly_rate': 80.0, 'efficiency': 1.0}
        }
        
        if not HAS_POSTGRES:
            return mock_rates.get(role)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT hourly_rate_nis, default_efficiency FROM rate_cards WHERE role = %s",
                        (role,)
                    )
                    rate_data = cursor.fetchone()
                    
                    if rate_data:
                        return {
                            'role': role,
                            'hourly_rate': float(rate_data[0]),
                            'efficiency': float(rate_data[1])
                        }
                    
                    return None
                    
        except Exception as e:
            print(f"Error getting labor rate: {e}")
            # Fall back to mock data
            return mock_rates.get(role)
    
    def estimate_shipping_cost(self, weight_kg: float, distance_km: float) -> Dict[str, Any]:
        """Estimate shipping cost based on weight and distance"""
        # Simple estimation model - in production, this would query shipping_quotes table
        base_fee = 50.0  # NIS
        per_km = 2.0     # NIS per km
        per_kg = 5.0     # NIS per kg
        
        cost = base_fee + (distance_km * per_km) + (weight_kg * per_kg)
        
        return {
            'base_fee': base_fee,
            'per_km_rate': per_km,
            'per_kg_rate': per_kg,
            'estimated_cost': cost,
            'confidence': 0.7
        }

# Global instance
pricing_resolver = PricingResolver()