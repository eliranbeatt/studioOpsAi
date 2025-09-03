"""Estimation schemas and models for shipping and labor"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class ShippingMethod(str, Enum):
    """Shipping method types"""
    STANDARD = "standard"
    EXPRESS = "express"
    FREIGHT = "freight"
    LOCAL = "local"

class ShippingEstimateRequest(BaseModel):
    """Request for shipping cost estimation"""
    weight_kg: float = Field(..., gt=0, description="Total weight in kilograms")
    distance_km: float = Field(..., gt=0, description="Distance in kilometers")
    method: ShippingMethod = Field(ShippingMethod.STANDARD, description="Shipping method")
    urgency: float = Field(1.0, ge=1.0, le=3.0, description="Urgency multiplier (1.0-3.0)")
    fragile: bool = Field(False, description="Whether items are fragile")
    insurance_value: Optional[float] = Field(None, ge=0, description="Insurance value in NIS")

class ShippingEstimate(BaseModel):
    """Shipping cost estimate"""
    base_cost: float = Field(..., description="Base shipping cost in NIS")
    distance_cost: float = Field(..., description="Cost based on distance")
    weight_cost: float = Field(..., description="Cost based on weight")
    urgency_surcharge: float = Field(0.0, description="Urgency surcharge")
    fragile_surcharge: float = Field(0.0, description="Fragile handling surcharge")
    insurance_cost: float = Field(0.0, description="Insurance cost")
    total_cost: float = Field(..., description="Total estimated cost in NIS")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of estimate")
    estimated_days: float = Field(..., description="Estimated delivery time in days")
    method: ShippingMethod = Field(..., description="Shipping method used")
    notes: Optional[str] = Field(None, description="Additional notes")

class LaborRole(str, Enum):
    """Labor role types"""
    CARPENTER = "carpenter"
    PAINTER = "painter"
    ELECTRICIAN = "electrician"
    PLUMBER = "plumber"
    LABORER = "laborer"
    PROJECT_MANAGER = "project_manager"
    DESIGNER = "designer"
    INSTALLER = "installer"

class LaborEstimateRequest(BaseModel):
    """Request for labor cost estimation"""
    role: LaborRole = Field(..., description="Labor role")
    hours_required: float = Field(..., gt=0, description="Estimated hours required")
    complexity: float = Field(1.0, ge=0.5, le=2.0, description="Complexity multiplier")
    location: Optional[str] = Field(None, description="Location for regional rates")
    overtime_hours: float = Field(0.0, ge=0, description="Overtime hours expected")
    tools_required: bool = Field(False, description="Whether special tools are required")

class LaborEstimate(BaseModel):
    """Labor cost estimate"""
    role: LaborRole = Field(..., description="Labor role")
    base_rate: float = Field(..., description="Base hourly rate in NIS")
    regular_hours: float = Field(..., description="Regular hours")
    regular_cost: float = Field(..., description="Cost for regular hours")
    overtime_hours: float = Field(0.0, description="Overtime hours")
    overtime_rate: float = Field(..., description="Overtime hourly rate")
    overtime_cost: float = Field(0.0, description="Cost for overtime hours")
    complexity_multiplier: float = Field(1.0, description="Complexity multiplier")
    tool_surcharge: float = Field(0.0, description="Tool surcharge")
    total_cost: float = Field(..., description="Total labor cost in NIS")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of estimate")
    estimated_days: float = Field(..., description="Estimated work duration in days")
    notes: Optional[str] = Field(None, description="Additional notes")

class MaterialRequirement(BaseModel):
    """Material requirement for estimation"""
    material_name: str = Field(..., description="Name of material")
    quantity: float = Field(..., gt=0, description="Quantity needed")
    unit: str = Field(..., description="Unit of measurement")
    waste_factor: float = Field(0.1, ge=0, le=1.0, description="Waste factor (0-1)")

class ProjectEstimateRequest(BaseModel):
    """Complete project estimation request"""
    project_id: Optional[UUID] = Field(None, description="Project ID if existing")
    materials: List[MaterialRequirement] = Field(..., description="List of material requirements")
    labor: List[LaborEstimateRequest] = Field(..., description="List of labor requirements")
    shipping: Optional[ShippingEstimateRequest] = Field(None, description="Shipping requirements")
    margin: float = Field(0.25, ge=0, le=1.0, description="Profit margin (0-1)")
    tax_rate: float = Field(0.17, ge=0, le=0.5, description="Tax rate (0-0.5)")

class ProjectEstimate(BaseModel):
    """Complete project cost estimate"""
    materials_cost: float = Field(0.0, description="Total materials cost in NIS")
    labor_cost: float = Field(0.0, description="Total labor cost in NIS")
    shipping_cost: float = Field(0.0, description="Total shipping cost in NIS")
    subtotal: float = Field(0.0, description="Subtotal before margin and tax")
    margin_amount: float = Field(0.0, description="Profit margin amount")
    tax_amount: float = Field(0.0, description="Tax amount")
    total_cost: float = Field(0.0, description="Total project cost in NIS")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence level")
    materials: List[Dict[str, Any]] = Field(..., description="Detailed material estimates")
    labor: List[LaborEstimate] = Field(..., description="Detailed labor estimates")
    shipping: Optional[ShippingEstimate] = Field(None, description="Shipping estimate if applicable")
    estimated_timeline_days: float = Field(0.0, description="Estimated project timeline in days")

class RateCardUpdate(BaseModel):
    """Rate card update model"""
    hourly_rate_nis: float = Field(..., gt=0, description="Hourly rate in NIS")
    default_efficiency: float = Field(1.0, ge=0.5, le=1.5, description="Default efficiency factor")
    overtime_rules: Optional[Dict[str, Any]] = Field(None, description="Overtime rules JSON")

class ShippingQuoteCreate(BaseModel):
    """Shipping quote creation model"""
    distance_km: float = Field(..., gt=0, description="Distance in kilometers")
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")
    method: ShippingMethod = Field(..., description="Shipping method")
    base_fee_nis: float = Field(..., description="Base fee in NIS")
    per_km_nis: float = Field(..., description="Cost per km in NIS")
    per_kg_nis: float = Field(..., description="Cost per kg in NIS")
    source: str = Field(..., description="Source of quote")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence level")
    surge_factors: Optional[Dict[str, Any]] = Field(None, description="Surge pricing factors")