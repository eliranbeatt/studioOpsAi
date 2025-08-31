// TypeScript interfaces for StudioOps AI plan data structures

export interface UnitPriceSource {
  vendor: string;
  confidence: number;
  fetched_at: string;
  sku?: string;
  vendor_rating?: number;
  is_quote?: boolean;
}

export interface PlanItem {
  category: 'materials' | 'labor' | 'tools' | 'logistics';
  title: string;
  description?: string;
  quantity: number;
  unit: string;
  unit_price: number;
  subtotal: number;
  
  // Material-specific properties
  unit_price_source?: UnitPriceSource;
  min_order?: number;
  lead_time_days?: number;
  
  // Labor-specific properties
  labor_role?: string;
  labor_hours?: number;
  experience_level?: string;
  specialties?: string[];
  min_hours?: number;
  overtime_rate?: number;
  travel_fee?: number;
  
  // Logistics-specific properties
  estimated_delivery?: string;
  weight_kg?: number;
  distance_km?: number;
  urgency?: string;
  material_type?: string;
}

export interface PlanMetadata {
  generated_at: number;
  items_count: number;
  materials_count: number;
  labor_count: number;
  project_type?: string;
  source?: string;
  margin_target?: number;
  currency?: string;
}

export interface Plan {
  project_id?: string;
  project_name: string;
  items: PlanItem[];
  total: number;
  margin_target: number;
  currency: string;
  metadata: PlanMetadata;
}

// API Response interfaces
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ChatMessage {
  message: string;
  project_id?: string;
  timestamp?: number;
}

export interface ChatResponse {
  message: string;
  context?: {
    assumptions: string[];
    risks: string[];
    suggestions: string[];
  };
  suggest_plan: boolean;
  timestamp: number;
}

// Estimation interfaces
export interface MaterialEstimate {
  material_name: string;
  estimated_quantity: number;
  unit: string;
  unit_price: number;
  estimated_cost: number;
  vendor: string;
  confidence: number;
  min_order: number;
  lead_time_days: number;
}

export interface LaborEstimate {
  role: string;
  estimated_hours: number;
  hourly_rate: number;
  estimated_cost: number;
  experience_level: string;
  specialties: string[];
  min_hours: number;
}

export interface ShippingEstimate {
  base_cost: number;
  final_cost: number;
  currency: string;
  weight_kg: number;
  distance_km: number;
  effective_distance_km: number;
  material_type: string;
  material_multiplier: number;
  urgency: string;
  urgency_multiplier: number;
  vendor_location: string;
  estimated_delivery: string;
  confidence: number;
  breakdown: {
    base_fee: number;
    distance_cost: number;
    weight_cost: number;
    material_surcharge: number;
    urgency_surcharge: number;
  };
}

// Mock data interfaces
export interface MockMaterialPrice {
  material_id: string;
  material_name: string;
  category: string;
  unit: string;
  price: number;
  confidence: number;
  fetched_at: string;
  vendor_name: string;
  vendor_rating: number;
  vendor_id: string;
  sku: string;
  is_quote: boolean;
  min_order: number;
  lead_time_days: number;
}

export interface MockLaborRate {
  role: string;
  hourly_rate: number;
  efficiency: number;
  experience_level: string;
  specialties: string[];
  vendor_id: string;
  min_hours: number;
  overtime_rate: number;
  travel_fee: number;
  license_number?: string;
}

// Request interfaces
export interface PlanRequest {
  project_id?: string;
  project_name?: string;
  project_description: string;
  materials?: string[];
  labor_roles?: string[];
}

export interface ShippingEstimateRequest {
  weight_kg: number;
  distance_km: number;
  urgency?: 'standard' | 'express' | 'priority' | 'same_day' | 'economy';
  material_type?: 'general' | 'fragile' | 'heavy' | 'bulky' | 'hazardous' | 'temperature_controlled';
  vendor_location?: 'local' | 'regional' | 'national';
}

export interface LaborEstimateRequest {
  role: string;
  project_description: string;
  materials_count: number;
}

export interface MaterialEstimateRequest {
  material_name: string;
  project_description: string;
}