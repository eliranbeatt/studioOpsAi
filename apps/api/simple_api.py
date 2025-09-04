#!/usr/bin/env python3
"""Simple FastAPI server without complex dependencies"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import json
import asyncio
import time
from datetime import datetime, timezone

# Database and AI services
try:
    from database import init_db
    from llm_service import llm_service
    from rag_service import rag_service
except ImportError:
    # Fallback for relative import
    from .database import init_db
    from .llm_service import llm_service
    from .rag_service import rag_service

app = FastAPI(
    title="StudioOps AI API",
    description="Core API for StudioOps AI project management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3005", "http://localhost:3006", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3005", "http://127.0.0.1:3006"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event - initialize database
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("Database initialized successfully")
        print("LLM service ready")
        print("RAG service ready")
    except Exception as e:
        print(f"Startup error: {e}")

# Mock data for pricing resolver
mock_prices = {
    # Wood & Lumber
    'Plywood 4x8': {
        'material_id': 'mock-plywood-id',
        'material_name': 'Plywood 4x8',
        'category': 'lumber',
        'unit': 'sheet',
        'price': 45.99,
        'confidence': 0.9,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Hardware Store',
        'vendor_rating': 4,
        'vendor_id': 'vendor-hw-001',
        'sku': 'PLY-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 1
    },
    '2x4 Lumber': {
        'material_id': 'mock-lumber-id',
        'material_name': '2x4 Lumber',
        'category': 'lumber',
        'unit': 'piece',
        'price': 8.99,
        'confidence': 0.9,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Lumber Yard',
        'vendor_rating': 5,
        'vendor_id': 'vendor-lum-001',
        'sku': 'LUM-001',
        'is_quote': False,
        'min_order': 10,
        'lead_time_days': 2
    },
    'Pine Board 1x6': {
        'material_id': 'mock-pineboard-id',
        'material_name': 'Pine Board 1x6',
        'category': 'lumber',
        'unit': 'linear_ft',
        'price': 3.50,
        'confidence': 0.8,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Lumber Yard',
        'vendor_rating': 5,
        'vendor_id': 'vendor-lum-001',
        'sku': 'PINE-001',
        'is_quote': False,
        'min_order': 8,
        'lead_time_days': 3
    },
    
    # Fasteners
    'Screws': {
        'material_id': 'mock-screws-id',
        'material_name': 'Construction Screws',
        'category': 'fasteners',
        'unit': 'box',
        'price': 12.99,
        'confidence': 0.85,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Hardware Store',
        'vendor_rating': 4,
        'vendor_id': 'vendor-hw-001',
        'sku': 'SCR-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 1
    },
    'Nails': {
        'material_id': 'mock-nails-id',
        'material_name': 'Common Nails',
        'category': 'fasteners',
        'unit': 'lb',
        'price': 25.00,
        'confidence': 0.75,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Hardware Store',
        'vendor_rating': 4,
        'vendor_id': 'vendor-hw-001',
        'sku': 'NAILS-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 1
    },
    
    # Finishes
    'Paint': {
        'material_id': 'mock-paint-id',
        'material_name': 'Interior Paint',
        'category': 'finishes',
        'unit': 'gallon',
        'price': 85.00,
        'confidence': 0.8,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Paint Store',
        'vendor_rating': 4,
        'vendor_id': 'vendor-paint-001',
        'sku': 'PAINT-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 1
    },
    'Stain': {
        'material_id': 'mock-stain-id',
        'material_name': 'Wood Stain',
        'category': 'finishes',
        'unit': 'quart',
        'price': 22.50,
        'confidence': 0.7,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Paint Store',
        'vendor_rating': 4,
        'vendor_id': 'vendor-paint-001',
        'sku': 'STAIN-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 2
    },
    
    # Hardware
    'Hinges': {
        'material_id': 'mock-hinges-id',
        'material_name': 'Cabinet Hinges',
        'category': 'hardware',
        'unit': 'pair',
        'price': 8.75,
        'confidence': 0.8,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Hardware Store',
        'vendor_rating': 4,
        'vendor_id': 'vendor-hw-001',
        'sku': 'HINGE-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 1
    },
    'Drawer Slides': {
        'material_id': 'mock-slides-id',
        'material_name': 'Drawer Slides',
        'category': 'hardware',
        'unit': 'pair',
        'price': 15.99,
        'confidence': 0.85,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Hardware Store',
        'vendor_rating': 4,
        'vendor_id': 'vendor-hw-001',
        'sku': 'SLIDE-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 3
    },
    
    # Electrical
    'Electrical Wire': {
        'material_id': 'mock-wire-id',
        'material_name': 'Electrical Wire',
        'category': 'electrical',
        'unit': 'roll',
        'price': 45.00,
        'confidence': 0.8,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Electrical Supply',
        'vendor_rating': 4,
        'vendor_id': 'vendor-elec-001',
        'sku': 'WIRE-001',
        'is_quote': False,
        'min_order': 1,
        'lead_time_days': 2
    },
    
    # Quotes (example of quoted items)
    'Custom Glass': {
        'material_id': 'mock-glass-id',
        'material_name': 'Custom Cut Glass',
        'category': 'specialty',
        'unit': 'sq_ft',
        'price': 35.00,
        'confidence': 0.6,
        'fetched_at': datetime.now(timezone.utc),
        'vendor_name': 'Glass Shop',
        'vendor_rating': 4,
        'vendor_id': 'vendor-glass-001',
        'sku': 'GLASS-001',
        'is_quote': True,
        'min_order': 5,
        'lead_time_days': 7
    }
}

mock_rates = {
    'Carpenter': {
        'role': 'Carpenter',
        'hourly_rate': 120.0,
        'efficiency': 0.9,
        'experience_level': 'Journeyman',
        'specialties': ['cabinetry', 'framing', 'finish work'],
        'vendor_id': 'labor-carp-001',
        'min_hours': 4,
        'overtime_rate': 180.0,
        'travel_fee': 50.0
    },
    'Master Carpenter': {
        'role': 'Master Carpenter',
        'hourly_rate': 150.0,
        'efficiency': 0.95,
        'experience_level': 'Master',
        'specialties': ['custom cabinetry', 'fine woodworking', 'restoration'],
        'vendor_id': 'labor-mcarp-001',
        'min_hours': 4,
        'overtime_rate': 225.0,
        'travel_fee': 75.0
    },
    'Painter': {
        'role': 'Painter',
        'hourly_rate': 100.0,
        'efficiency': 0.8,
        'experience_level': 'Journeyman',
        'specialties': ['interior painting', 'trim work', 'spray finishing'],
        'vendor_id': 'labor-paint-001',
        'min_hours': 4,
        'overtime_rate': 150.0,
        'travel_fee': 40.0
    },
    'Electrician': {
        'role': 'Electrician',
        'hourly_rate': 150.0,
        'efficiency': 0.85,
        'experience_level': 'Licensed',
        'specialties': ['residential wiring', 'lighting installation', 'panel upgrades'],
        'vendor_id': 'labor-elec-001',
        'min_hours': 2,
        'overtime_rate': 225.0,
        'travel_fee': 75.0,
        'license_number': 'ELEC-12345'
    },
    'Plumber': {
        'role': 'Plumber',
        'hourly_rate': 140.0,
        'efficiency': 0.85,
        'experience_level': 'Licensed',
        'specialties': ['fixture installation', 'drain cleaning', 'water lines'],
        'vendor_id': 'labor-plumb-001',
        'min_hours': 2,
        'overtime_rate': 210.0,
        'travel_fee': 65.0,
        'license_number': 'PLMB-67890'
    },
    'Laborer': {
        'role': 'Laborer',
        'hourly_rate': 80.0,
        'efficiency': 1.0,
        'experience_level': 'Helper',
        'specialties': ['demolition', 'cleanup', 'material handling'],
        'vendor_id': 'labor-help-001',
        'min_hours': 4,
        'overtime_rate': 120.0,
        'travel_fee': 30.0
    },
    'Tile Setter': {
        'role': 'Tile Setter',
        'hourly_rate': 110.0,
        'efficiency': 0.75,
        'experience_level': 'Journeyman',
        'specialties': ['floor tiling', 'backslash installation', 'shower surrounds'],
        'vendor_id': 'labor-tile-001',
        'min_hours': 4,
        'overtime_rate': 165.0,
        'travel_fee': 50.0
    },
    'Drywaller': {
        'role': 'Drywaller',
        'hourly_rate': 95.0,
        'efficiency': 0.7,
        'experience_level': 'Journeyman',
        'specialties': ['drywall installation', 'taping', 'texturing'],
        'vendor_id': 'labor-drywall-001',
        'min_hours': 4,
        'overtime_rate': 142.5,
        'travel_fee': 45.0
    }
}

class ChatMessage:
    message: str
    project_id: Optional[str] = None

async def simulate_ai_response(message: str):
    """Simulate AI response generation with advanced context detection"""
    
    message_lower = message.lower()
    
    # Comprehensive project type detection
    project_types = {
        'cabinet': {
            'keywords': ['cabinet', 'cupboard', 'storage', 'kitchen', 'bathroom', 'vanity', 'drawer', 'shelf'],
            'materials': ['Plywood 4x8', '2x4 Lumber', 'Screws', 'Hinges', 'Drawer Slides', 'Paint', 'Stain'],
            'labor': ['Carpenter', 'Painter'],
            'complexity': 'medium'
        },
        'furniture': {
            'keywords': ['table', 'chair', 'desk', 'shelf', 'bookshelf', 'bench', 'bed', 'furniture', 'sofa'],
            'materials': ['Plywood 4x8', '2x4 Lumber', 'Pine Board 1x6', 'Screws', 'Hinges', 'Paint', 'Stain'],
            'labor': ['Carpenter'],
            'complexity': 'medium'
        },
        'painting': {
            'keywords': ['paint', 'painting', 'color', 'wall', 'ceiling', 'trim', 'exterior', 'interior', 'finish'],
            'materials': ['Paint', 'Stain'],
            'labor': ['Painter', 'Laborer'],
            'complexity': 'low'
        },
        'electrical': {
            'keywords': ['electrical', 'wiring', 'outlet', 'switch', 'light', 'fixture', 'panel', 'circuit', 'breaker'],
            'materials': ['Electrical Wire'],
            'labor': ['Electrician'],
            'complexity': 'high'
        },
        'plumbing': {
            'keywords': ['plumbing', 'pipe', 'faucet', 'sink', 'toilet', 'shower', 'drain', 'water', 'valve'],
            'materials': [],  # Plumbing materials not in mock data
            'labor': ['Plumber'],
            'complexity': 'high'
        },
        'renovation': {
            'keywords': ['renovate', 'remodel', 'update', 'modernize', 'refresh', 'renovation', 'remodeling'],
            'materials': ['Plywood 4x8', '2x4 Lumber', 'Screws', 'Paint', 'Electrical Wire'],
            'labor': ['Carpenter', 'Painter', 'Electrician', 'Laborer'],
            'complexity': 'high'
        },
        'construction': {
            'keywords': ['build', 'construct', 'frame', 'structure', 'foundation', 'deck', 'patio'],
            'materials': ['Plywood 4x8', '2x4 Lumber', 'Screws', 'Nails'],
            'labor': ['Carpenter', 'Laborer'],
            'complexity': 'medium'
        }
    }
    
    # Material detection with specific products
    materials = {
        'lumber': ['wood', 'lumber', 'plywood', 'board', '2x4', 'pine', 'oak', 'maple', 'timber'],
        'fasteners': ['screw', 'nail', 'bolt', 'hinge', 'bracket', 'hardware', 'fastener'],
        'finishes': ['paint', 'stain', 'varnish', 'sealer', 'primer', 'finish', 'coating'],
        'electrical': ['wire', 'cable', 'conduit', 'breaker', 'outlet', 'switch', 'electrical'],
        'plumbing': ['pipe', 'fitting', 'valve', 'faucet', 'drain', 'plumbing'],
        'hardware': ['handle', 'knob', 'pull', 'lock', 'latch', 'hardware']
    }
    
    # Project attributes detection
    project_attributes = {
        'size': {
            'small': ['small', 'compact', 'tiny', 'minor', 'single', 'basic'],
            'medium': ['medium', 'average', 'standard', 'normal', 'typical'],
            'large': ['large', 'big', 'extensive', 'major', 'whole', 'complete', 'full']
        },
        'complexity': {
            'simple': ['simple', 'basic', 'straightforward', 'easy', 'standard'],
            'moderate': ['moderate', 'average', 'typical', 'regular'],
            'complex': ['complex', 'detailed', 'intricate', 'custom', 'precision', 'advanced', 'sophisticated']
        },
        'urgency': {
            'normal': ['normal', 'standard', 'regular', 'whenever'],
            'urgent': ['urgent', 'quick', 'fast', 'soon', 'asap', 'priority'],
            'relaxed': ['relaxed', 'flexible', 'whenever', 'no rush']
        }
    }
    
    detected_project_type = None
    detected_materials = []
    detected_size = 'medium'
    detected_complexity = 'moderate'
    detected_urgency = 'normal'
    
    # Detect project type with confidence scoring
    project_type_scores = {}
    for p_type, data in project_types.items():
        score = 0
        for keyword in data['keywords']:
            if keyword in message_lower:
                score += 1
                # Bonus for exact matches
                if f' {keyword} ' in f' {message_lower} ':
                    score += 2
        
        if score > 0:
            project_type_scores[p_type] = score
    
    if project_type_scores:
        detected_project_type = max(project_type_scores.items(), key=lambda x: x[1])[0]
    
    # Detect materials
    for material_type, keywords in materials.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_materials.append(material_type)
    
    # Detect project attributes
    for attr_type, levels in project_attributes.items():
        for level, keywords in levels.items():
            if any(keyword in message_lower for keyword in keywords):
                if attr_type == 'size':
                    detected_size = level
                elif attr_type == 'complexity':
                    detected_complexity = level
                elif attr_type == 'urgency':
                    detected_urgency = level
    
    # Generate context-aware response with detailed project understanding
    if "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
        return "Hello! I'm StudioOps AI. How can I help you with your project today?"
    
    elif "help" in message_lower or "assist" in message_lower:
        return "I'd be happy to help! I can assist with project planning, material pricing, labor estimates, and creating detailed work plans. What type of project are you working on?"
    
    elif detected_project_type:
        project_data = project_types[detected_project_type]
        
        response = f"Excellent! I see you're working on a {detected_size} {detected_project_type} project."
        
        if detected_complexity != 'moderate':
            response += f" This sounds like a {detected_complexity} project."
        
        response += "\n\nI recommend:"
        
        # Add material recommendations
        if project_data['materials']:
            response += "\n• " + ", ".join(project_data['materials'][:3])
            if len(project_data['materials']) > 3:
                response += f" and {len(project_data['materials']) - 3} more materials"
        
        # Add labor recommendations
        if project_data['labor']:
            response += "\n• " + ", ".join(project_data['labor']) + " services"
        
        # Add complexity-specific advice
        if detected_complexity == 'complex':
            response += "\n• Professional installation recommended"
        elif detected_complexity == 'simple':
            response += "\n• DIY-friendly approach possible"
        
        response += "\n\nI can create a detailed plan with current pricing and accurate estimates. Would you like me to generate a project plan?"
        
        return response
    
    elif "price" in message_lower or "cost" in message_lower or "how much":
        if detected_materials:
            materials_list = ", ".join(detected_materials)
            return f"I can provide real-time pricing for {materials_list}. I have access to current vendor databases with confidence scores. Would you like specific price quotes?"
        else:
            return "I can help with pricing for various construction materials and labor services. What specific items or services are you looking to price?"
    
    elif "plan" in message_lower or "schedule" in message_lower or "timeline":
        response = "I can create comprehensive project plans including:"
        response += "\n• Material lists with current vendor pricing"
        response += "\n• Labor estimates with role-based rates"
        response += "\n• Timeline projections based on complexity"
        response += "\n• Detailed cost breakdowns"
        
        if detected_urgency == 'urgent':
            response += "\n• Expedited scheduling options"
        
        response += "\n\nJust describe your project and I'll generate a detailed plan!"
        return response
    
    elif "estimate" in message_lower or "quote" in message_lower:
        return (
            "I can provide accurate estimates based on:"
            "\n• Current material prices from multiple vendors"
            "\n• Labor rates by experience level"
            "\n• Project size and complexity factors"
            "\n• Shipping and logistics costs"
            "\n\nWhat would you like me to estimate?"
        )
    
    elif "thank" in message_lower or "thanks":
        return "You're welcome! I'm here to help with all your project management needs. Let me know if you need anything else!"
    
    else:
        return (
            "I'm StudioOps AI, your project management assistant! I can help with:"
            "\n• Project planning and material selection"
            "\n• Real-time pricing from vendor databases"
            "\n• Labor cost estimation with experience levels"
            "\n• Work plan generation with timeline scheduling"
            "\n• Cost breakdowns and budget planning"
            "\n\nWhat would you like to work on today?"
        )


def get_material_price(material_name: str) -> Optional[Dict[str, Any]]:
    """Get material price from mock data"""
    return mock_prices.get(material_name)

def get_labor_rate(role: str) -> Optional[Dict[str, Any]]:
    """Get labor rate from mock data"""
    return mock_rates.get(role)

def estimate_shipping_cost(weight_kg: float, distance_km: float, urgency: str = 'standard', 
                          material_type: str = 'general', vendor_location: str = 'local') -> Dict[str, Any]:
    """Estimate shipping cost with configurable rates and modifiers"""
    
    # Base rates by vendor location
    base_rates = {
        'local': {
            'base_fee': 50.0,
            'per_km': 1.5,
            'per_kg': 4.0,
            'min_distance': 0,
            'max_distance': 100
        },
        'regional': {
            'base_fee': 100.0,
            'per_km': 1.2,
            'per_kg': 3.5,
            'min_distance': 50,
            'max_distance': 300
        },
        'national': {
            'base_fee': 200.0,
            'per_km': 0.8,
            'per_kg': 3.0,
            'min_distance': 200,
            'max_distance': 1000
        }
    }
    
    # Material type multipliers
    material_multipliers = {
        'general': 1.0,
        'fragile': 1.8,      # Glass, ceramics, delicate items
        'heavy': 1.4,        # Metal, stone, dense materials
        'bulky': 1.6,        # Large items, furniture
        'hazardous': 2.5,    # Chemicals, flammable materials
        'temperature_controlled': 2.2  # Refrigerated items
    }
    
    # Urgency multipliers
    urgency_multipliers = {
        'standard': 1.0,     # 3-5 business days
        'express': 1.8,      # 1-2 business days
        'priority': 2.5,     # Next day
        'same_day': 4.0,     # Same day delivery
        'economy': 0.7       # 5-7 business days
    }
    
    # Get base rates for vendor location
    rates = base_rates.get(vendor_location, base_rates['local'])
    
    # Apply distance constraints
    effective_distance = max(rates['min_distance'], min(distance_km, rates['max_distance']))
    
    # Calculate base cost
    base_cost = rates['base_fee'] + (effective_distance * rates['per_km']) + (weight_kg * rates['per_kg'])
    
    # Apply material type multiplier
    material_multiplier = material_multipliers.get(material_type, 1.0)
    
    # Apply urgency multiplier
    urgency_multiplier = urgency_multipliers.get(urgency, 1.0)
    
    # Calculate final cost
    final_cost = base_cost * material_multiplier * urgency_multiplier
    
    # Calculate confidence based on input quality
    confidence = 0.8
    if weight_kg <= 0 or distance_km <= 0:
        confidence = 0.5  # Low confidence for invalid inputs
    elif weight_kg > 1000 or distance_km > 500:
        confidence = 0.6  # Medium confidence for extreme values
    
    # Determine estimated delivery time based on urgency and distance
    delivery_times = {
        'same_day': '4-8 hours',
        'priority': '24 hours',
        'express': '2-3 days',
        'standard': '3-5 days',
        'economy': '5-7 days'
    }
    
    # Adjust delivery time for long distances
    estimated_delivery = delivery_times.get(urgency, '3-5 days')
    if distance_km > 300 and urgency != 'same_day':
        # Add extra days for long distances
        if urgency == 'priority':
            estimated_delivery = '2-3 days'
        elif urgency == 'express':
            estimated_delivery = '3-4 days'
        elif urgency == 'standard':
            estimated_delivery = '5-7 days'
        elif urgency == 'economy':
            estimated_delivery = '7-10 days'
    
    return {
        'base_cost': round(base_cost, 2),
        'final_cost': round(final_cost, 2),
        'currency': 'NIS',
        'weight_kg': weight_kg,
        'distance_km': distance_km,
        'effective_distance_km': effective_distance,
        'material_type': material_type,
        'material_multiplier': material_multiplier,
        'urgency': urgency,
        'urgency_multiplier': urgency_multiplier,
        'vendor_location': vendor_location,
        'estimated_delivery': estimated_delivery,
        'confidence': confidence,
        'breakdown': {
            'base_fee': rates['base_fee'],
            'distance_cost': effective_distance * rates['per_km'],
            'weight_cost': weight_kg * rates['per_kg'],
            'material_surcharge': base_cost * (material_multiplier - 1),
            'urgency_surcharge': (base_cost * material_multiplier) * (urgency_multiplier - 1)
        }
    }

def _estimate_material_quantity(material_name: str, project_description: str) -> float:
    """Estimate material quantity based on project type, size, and complexity"""
    
    # Base estimates for different project types
    project_estimates = {
        'cabinet': {
            'Plywood 4x8': 6.0,    # sheets for standard cabinet
            '2x4 Lumber': 8.0,     # pieces for framing
            'Pine Board 1x6': 16.0, # linear feet for face frames
            'Screws': 1.5,         # boxes
            'Hinges': 8.0,         # pairs for doors
            'Drawer Slides': 4.0,  # pairs
            'Paint': 0.5,          # gallons for finishing
            'Stain': 0.3           # quarts
        },
        'furniture': {
            'Plywood 4x8': 3.0,
            '2x4 Lumber': 12.0,
            'Pine Board 1x6': 20.0,
            'Screws': 1.0,
            'Hinges': 4.0,
            'Paint': 0.3,
            'Stain': 0.2
        },
        'painting': {
            'Paint': 2.0,          # gallons per room
            'Stain': 0.5           # quarts for trim
        },
        'electrical': {
            'Electrical Wire': 1.0 # rolls
        },
        'default': {
            'Plywood 4x8': 8.0,
            '2x4 Lumber': 20.0,
            'Screws': 2.0,
            'Nails': 1.0,
            'Paint': 3.0,
            'Stain': 0.5,
            'Hinges': 6.0,
            'Drawer Slides': 3.0,
            'Electrical Wire': 0.5
        }
    }
    
    # Detect project type from description
    desc_lower = project_description.lower()
    project_type = 'default'
    
    if any(word in desc_lower for word in ['cabinet', 'cupboard', 'vanity', 'storage']):
        project_type = 'cabinet'
    elif any(word in desc_lower for word in ['furniture', 'table', 'chair', 'desk', 'shelf']):
        project_type = 'furniture'
    elif any(word in desc_lower for word in ['paint', 'painting', 'wall', 'ceiling']):
        project_type = 'painting'
    elif any(word in desc_lower for word in ['electrical', 'wiring', 'light', 'outlet']):
        project_type = 'electrical'
    
    # Get base estimate
    estimates = project_estimates[project_type]
    base_quantity = estimates.get(material_name, 1.0)
    
    # Apply size modifiers
    size_multiplier = 1.0
    if any(word in desc_lower for word in ['large', 'big', 'extensive', 'major']):
        size_multiplier = 1.8
    elif any(word in desc_lower for word in ['small', 'simple', 'basic', 'minor']):
        size_multiplier = 0.6
    elif any(word in desc_lower for word in ['medium', 'average', 'standard']):
        size_multiplier = 1.0
    
    # Apply complexity modifiers
    complexity_multiplier = 1.0
    if any(word in desc_lower for word in ['complex', 'detailed', 'intricate', 'custom']):
        complexity_multiplier = 1.5
    elif any(word in desc_lower for word in ['simple', 'basic', 'straightforward']):
        complexity_multiplier = 0.8
    
    # Calculate final quantity
    final_quantity = base_quantity * size_multiplier * complexity_multiplier
    
    # Round to appropriate precision
    if material_name in ['Paint', 'Stain']:
        return round(final_quantity, 1)  # 0.1 precision for liquids
    elif material_name in ['Plywood 4x8', '2x4 Lumber']:
        return round(final_quantity)     # whole units for large items
    else:
        return round(final_quantity, 1)  # 0.1 precision for others

def _estimate_labor_hours(role: str, project_description: str, materials_count: int) -> float:
    """Estimate labor hours based on role, project complexity, and experience level"""
    
    # Base hours by role and experience level
    base_hours = {
        'Carpenter': {
            'Master': 12.0,    # Master carpenters are more efficient
            'Journeyman': 16.0,
            'Helper': 20.0     # Helpers take longer
        },
        'Master Carpenter': {
            'Master': 10.0,
            'Journeyman': 14.0,
            'Helper': 18.0
        },
        'Painter': {
            'Master': 6.0,
            'Journeyman': 8.0,
            'Helper': 12.0
        },
        'Electrician': {
            'Licensed': 5.0,
            'Journeyman': 7.0,
            'Helper': 10.0
        },
        'Plumber': {
            'Licensed': 6.0,
            'Journeyman': 8.0,
            'Helper': 12.0
        },
        'Laborer': {
            'Helper': 12.0,
            'Journeyman': 10.0,
            'Master': 8.0
        },
        'Tile Setter': {
            'Master': 8.0,
            'Journeyman': 12.0,
            'Helper': 16.0
        },
        'Drywaller': {
            'Master': 6.0,
            'Journeyman': 10.0,
            'Helper': 14.0
        }
    }
    
    # Get experience level from labor data
    labor_data = mock_rates.get(role)
    experience_level = labor_data.get('experience_level', 'Journeyman') if labor_data else 'Journeyman'
    
    # Get base hours for this role and experience level
    role_base = base_hours.get(role, {'Journeyman': 8.0})
    hours = role_base.get(experience_level, role_base.get('Journeyman', 8.0))
    
    desc_lower = project_description.lower()
    
    # Project complexity modifiers
    complexity_multiplier = 1.0
    if any(word in desc_lower for word in ['complex', 'detailed', 'intricate', 'custom', 'precision']):
        complexity_multiplier = 1.6
    elif any(word in desc_lower for word in ['simple', 'basic', 'straightforward', 'standard']):
        complexity_multiplier = 0.7
    elif any(word in desc_lower for word in ['moderate', 'average', 'typical']):
        complexity_multiplier = 1.0
    
    # Project size modifiers
    size_multiplier = 1.0
    if any(word in desc_lower for word in ['large', 'big', 'extensive', 'major', 'whole house']):
        size_multiplier = 1.8
    elif any(word in desc_lower for word in ['small', 'compact', 'minor', 'single room']):
        size_multiplier = 0.6
    elif any(word in desc_lower for word in ['medium', 'average', 'normal']):
        size_multiplier = 1.0
    
    # Material complexity modifiers
    material_multiplier = 1.0
    if materials_count > 8:
        material_multiplier = 1.4
    elif materials_count > 5:
        material_multiplier = 1.2
    elif materials_count < 3:
        material_multiplier = 0.8
    
    # Specialization bonuses - certain roles are more efficient for specific project types
    specialization_bonus = 1.0
    if labor_data and 'specialties' in labor_data:
        specialties = labor_data['specialties']
        
        if 'cabinet' in desc_lower and any(spec in specialties for spec in ['cabinetry', 'custom cabinetry', 'fine woodworking']):
            specialization_bonus = 0.8  # 20% more efficient
        elif 'painting' in desc_lower and any(spec in specialties for spec in ['interior painting', 'spray finishing']):
            specialization_bonus = 0.85
        elif 'electrical' in desc_lower and any(spec in specialties for spec in ['residential wiring', 'lighting installation']):
            specialization_bonus = 0.9
    
    # Calculate final hours
    final_hours = hours * complexity_multiplier * size_multiplier * material_multiplier * specialization_bonus
    
    # Apply minimum hours based on role
    min_hours = labor_data.get('min_hours', 4.0) if labor_data else 4.0
    final_hours = max(final_hours, min_hours)
    
    return round(final_hours, 1)

@app.get("/")
async def root():
    return {"message": "StudioOps AI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "studioops-api"}

@app.post("/chat/message")
async def chat_message(chat_message: dict):
    """Real chat endpoint with LLM integration and memory"""
    try:
        # LLM services are already imported globally
        
        message = chat_message.get('message', '')
        session_id = chat_message.get('session_id')
        project_context = chat_message.get('project_context', {})
        
        # Enhance message with RAG context
        enhanced_message = rag_service.enhance_prompt(message)
        
        # Get AI response with memory
        response = await llm_service.generate_response(
            enhanced_message, 
            session_id, 
            project_context
        )
        
        return {
            "message": response["message"],
            "context": {
                "assumptions": ["Using current material prices", "Standard labor rates applied"],
                "risks": ["Material availability may vary", "Labor rates subject to change"],
                "suggestions": ["Consider getting multiple quotes", "Allow for 15% contingency"]
            },
            "suggest_plan": response["suggest_plan"],
            "session_id": response["session_id"],
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {e}")

@app.get("/context/detect")
async def detect_context(message: str):
    """Analyze message and detect project context"""
    try:
        message_lower = message.lower()
        
        # Reuse the detection logic from simulate_ai_response
        project_types = {
            'cabinet': ['cabinet', 'cupboard', 'storage', 'kitchen', 'bathroom', 'vanity', 'drawer', 'shelf'],
            'furniture': ['table', 'chair', 'desk', 'shelf', 'bookshelf', 'bench', 'bed', 'furniture', 'sofa'],
            'painting': ['paint', 'painting', 'color', 'wall', 'ceiling', 'trim', 'exterior', 'interior', 'finish'],
            'electrical': ['electrical', 'wiring', 'outlet', 'switch', 'light', 'fixture', 'panel', 'circuit', 'breaker'],
            'plumbing': ['plumbing', 'pipe', 'faucet', 'sink', 'toilet', 'shower', 'drain', 'water', 'valve'],
            'renovation': ['renovate', 'remodel', 'update', 'modernize', 'refresh', 'renovation', 'remodeling'],
            'construction': ['build', 'construct', 'frame', 'structure', 'foundation', 'deck', 'patio']
        }
        
        materials = {
            'lumber': ['wood', 'lumber', 'plywood', 'board', '2x4', 'pine', 'oak', 'maple', 'timber'],
            'fasteners': ['screw', 'nail', 'bolt', 'hinge', 'bracket', 'hardware', 'fastener'],
            'finishes': ['paint', 'stain', 'varnish', 'sealer', 'primer', 'finish', 'coating'],
            'electrical': ['wire', 'cable', 'conduit', 'breaker', 'outlet', 'switch', 'electrical'],
            'plumbing': ['pipe', 'fitting', 'valve', 'faucet', 'drain', 'plumbing'],
            'hardware': ['handle', 'knob', 'pull', 'lock', 'latch', 'hardware']
        }
        
        project_attributes = {
            'size': {
                'small': ['small', 'compact', 'tiny', 'minor', 'single', 'basic'],
                'medium': ['medium', 'average', 'standard', 'normal', 'typical'],
                'large': ['large', 'big', 'extensive', 'major', 'whole', 'complete', 'full']
            },
            'complexity': {
                'simple': ['simple', 'basic', 'straightforward', 'easy', 'standard'],
                'moderate': ['moderate', 'average', 'typical', 'regular'],
                'complex': ['complex', 'detailed', 'intricate', 'custom', 'precision', 'advanced', 'sophisticated']
            },
            'urgency': {
                'normal': ['normal', 'standard', 'regular', 'whenever'],
                'urgent': ['urgent', 'quick', 'fast', 'soon', 'asap', 'priority'],
                'relaxed': ['relaxed', 'flexible', 'whenever', 'no rush']
            }
        }
        
        # Detect project type with confidence scoring
        project_type_scores = {}
        for p_type, keywords in project_types.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
                    if f' {keyword} ' in f' {message_lower} ':
                        score += 2
            if score > 0:
                project_type_scores[p_type] = score
        
        detected_project_type = max(project_type_scores.items(), key=lambda x: x[1])[0] if project_type_scores else None
        
        # Detect materials
        detected_materials = []
        for material_type, keywords in materials.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_materials.append(material_type)
        
        # Detect project attributes
        detected_attributes = {}
        for attr_type, levels in project_attributes.items():
            for level, keywords in levels.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_attributes[attr_type] = level
        
        return {
            "success": True,
            "analysis": {
                "message": message,
                "detected_project_type": detected_project_type,
                "project_type_confidence": project_type_scores,
                "detected_materials": detected_materials,
                "detected_attributes": detected_attributes,
                "recommended_materials": [],
                "recommended_labor": []
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing context: {e}")

@app.get("/demo/test-all")
async def test_all_functionality():
    """Test all mock functionality with comprehensive demo"""
    try:
        # Test chat response
        chat_response = await simulate_ai_response("I want to build custom kitchen cabinets")
        
        # Test material estimation
        material_estimates = []
        test_materials = ['Plywood 4x8', '2x4 Lumber', 'Screws', 'Paint']
        for material in test_materials:
            quantity = _estimate_material_quantity(material, "custom kitchen cabinets complex project")
            price_data = get_material_price(material)
            material_estimates.append({
                'material': material,
                'quantity': quantity,
                'unit_price': price_data['price'] if price_data else 0,
                'estimated_cost': quantity * (price_data['price'] if price_data else 0)
            })
        
        # Test labor estimation
        labor_estimates = []
        test_roles = ['Carpenter', 'Painter']
        for role in test_roles:
            hours = _estimate_labor_hours(role, "custom kitchen cabinets complex project", len(test_materials))
            labor_data = get_labor_rate(role)
            labor_estimates.append({
                'role': role,
                'hours': hours,
                'hourly_rate': labor_data['hourly_rate'] if labor_data else 0,
                'total': hours * (labor_data['hourly_rate'] if labor_data else 0)
            })
        
        # Test shipping
        shipping_data = estimate_shipping_cost(150, 25, 'standard', 'general', 'local')
        
        return {
            "success": True,
            "demo": {
                "chat_response": chat_response,
                "material_estimates": material_estimates,
                "labor_estimates": labor_estimates,
                "shipping_estimate": shipping_data,
                "total_project_cost": (
                    sum(m['estimated_cost'] for m in material_estimates) +
                    sum(l['total'] for l in labor_estimates) +
                    shipping_data['final_cost']
                )
            },
            "available_materials": list(mock_prices.keys()),
            "available_labor_roles": list(mock_rates.keys())
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in demo: {e}")

@app.get("/materials/estimate")
async def estimate_material_endpoint(
    material_name: str,
    project_description: str
):
    """Estimate material quantity for a specific project"""
    try:
        quantity = _estimate_material_quantity(material_name, project_description)
        price_data = get_material_price(material_name)
        
        return {
            "success": True,
            "data": {
                "material_name": material_name,
                "estimated_quantity": quantity,
                "unit": price_data['unit'] if price_data else 'unit',
                "unit_price": price_data['price'] if price_data else 0,
                "estimated_cost": quantity * (price_data['price'] if price_data else 0),
                "vendor": price_data['vendor_name'] if price_data else 'Unknown',
                "confidence": price_data['confidence'] if price_data else 0.5,
                "min_order": price_data.get('min_order', 1) if price_data else 1,
                "lead_time_days": price_data.get('lead_time_days', 3) if price_data else 3
            },
            "parameters": {
                "material_name": material_name,
                "project_description": project_description
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating material: {e}")

@app.get("/labor/estimate")
async def estimate_labor_endpoint(
    role: str,
    project_description: str,
    materials_count: int
):
    """Estimate labor hours for a specific role and project"""
    try:
        hours = _estimate_labor_hours(role, project_description, materials_count)
        labor_data = get_labor_rate(role)
        
        return {
            "success": True,
            "data": {
                "role": role,
                "estimated_hours": hours,
                "hourly_rate": labor_data['hourly_rate'] if labor_data else 0,
                "estimated_cost": hours * (labor_data['hourly_rate'] if labor_data else 0),
                "experience_level": labor_data.get('experience_level', 'Unknown') if labor_data else 'Unknown',
                "specialties": labor_data.get('specialties', []) if labor_data else [],
                "min_hours": labor_data.get('min_hours', 4) if labor_data else 4
            },
            "parameters": {
                "role": role,
                "project_description": project_description,
                "materials_count": materials_count
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating labor: {e}")

@app.get("/shipping/estimate")
async def estimate_shipping_endpoint(
    weight_kg: float,
    distance_km: float,
    urgency: str = 'standard',
    material_type: str = 'general',
    vendor_location: str = 'local'
):
    """Estimate shipping costs with detailed parameters"""
    try:
        shipping_data = estimate_shipping_cost(
            weight_kg=weight_kg,
            distance_km=distance_km,
            urgency=urgency,
            material_type=material_type,
            vendor_location=vendor_location
        )
        
        return {
            "success": True,
            "data": shipping_data,
            "parameters": {
                "weight_kg": weight_kg,
                "distance_km": distance_km,
                "urgency": urgency,
                "material_type": material_type,
                "vendor_location": vendor_location
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating shipping: {e}")

@app.post("/chat/generate_plan")
async def generate_plan_skeleton(plan_request: dict):
    """Generate a plan skeleton from chat context"""
    try:
        project_name = plan_request.get('project_name', 'New Project')
        project_description = plan_request.get('project_description', '')
        
        materials_to_include = []
        
        if 'cabinet' in project_description.lower() or 'furniture' in project_description.lower():
            materials_to_include = ['Plywood 4x8', '2x4 Lumber', 'Screws']
        elif 'painting' in project_description.lower():
            materials_to_include = ['Paint']
        else:
            materials_to_include = ['Plywood 4x8', '2x4 Lumber', 'Screws', 'Nails']
        
        items = []
        total = 0.0
        
        for material_name in materials_to_include:
            price_data = get_material_price(material_name)
            if price_data:
                quantity = _estimate_material_quantity(material_name, project_description)
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
        
        labor_roles = ['Carpenter']
        if 'painting' in project_description.lower():
            labor_roles.append('Painter')
        if 'electrical' in project_description.lower():
            labor_roles.append('Electrician')
        
        for role in labor_roles:
            labor_data = get_labor_rate(role)
            if labor_data:
                hours = _estimate_labor_hours(role, project_description, len(materials_to_include))
                subtotal = hours * labor_data['hourly_rate']
                
                items.append({
                    "category": "labor",
                    "title": f"{role} work",
                    "description": f"{role} services for {project_name}",
                    "quantity": hours,
                    "unit": "hour",
                    "unit_price": labor_data['hourly_rate'],
                    "labor_role": role,
                    "labor_hours": hours,
                    "subtotal": round(subtotal, 2)
                })
                total += subtotal
        
        shipping_data = estimate_shipping_cost(
            weight_kg=100, 
            distance_km=50, 
            urgency='standard', 
            material_type='general', 
            vendor_location='local'
        )
        items.append({
            "category": "logistics",
            "title": "Shipping & Delivery",
            "description": "Material delivery and logistics",
            "quantity": 1,
            "unit": "delivery",
            "unit_price": shipping_data['final_cost'],
            "subtotal": round(shipping_data['final_cost'], 2)
        })
        total += shipping_data['final_cost']
        
        plan_skeleton = {
            "project_id": plan_request.get('project_id'),
            "project_name": project_name,
            "items": items,
            "total": round(total, 2),
            "margin_target": 0.25,
            "currency": "NIS",
            "metadata": {
                "generated_at": time.time(),
                "items_count": len(items),
                "materials_count": len([i for i in items if i['category'] == 'materials']),
                "labor_count": len([i for i in items if i['category'] == 'labor'])
            }
        }
        
        return plan_skeleton
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {e}")

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Get port from command line or use 8003
    port = 8003
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        try:
            port = int(sys.argv[2])
        except (IndexError, ValueError):
            pass
    
    uvicorn.run(app, host="0.0.0.0", port=port)