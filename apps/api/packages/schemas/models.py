from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class VendorBase(BaseModel):
    name: str = Field(..., description="Vendor name")
    contact: Optional[dict] = Field(None, description="Contact information")
    url: Optional[str] = Field(None, description="Vendor website URL")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    notes: Optional[str] = Field(None, description="Additional notes")

class VendorCreate(VendorBase):
    pass

class VendorUpdate(VendorBase):
    pass

class Vendor(VendorBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MaterialBase(BaseModel):
    name: str = Field(..., description="Material name")
    spec: Optional[str] = Field(None, description="Material specification")
    unit: str = Field(..., description="Unit of measurement")
    category: Optional[str] = Field(None, description="Material category")
    typical_waste_pct: float = Field(0.0, ge=0, le=100, description="Typical waste percentage")
    notes: Optional[str] = Field(None, description="Additional notes")

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(MaterialBase):
    pass

class Material(MaterialBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VendorPriceBase(BaseModel):
    vendor_id: UUID = Field(..., description="Vendor ID")
    material_id: UUID = Field(..., description="Material ID")
    sku: Optional[str] = Field(None, description="SKU or product code")
    price_nis: float = Field(..., ge=0, description="Price in NIS")
    source_url: Optional[str] = Field(None, description="Source URL for price")
    confidence: float = Field(0.8, ge=0, le=1, description="Confidence level (0-1)")
    is_quote: bool = Field(False, description="Whether this is a quote price")

class VendorPriceCreate(VendorPriceBase):
    pass

class VendorPriceUpdate(VendorPriceBase):
    pass

class VendorPrice(VendorPriceBase):
    id: UUID
    fetched_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class PurchaseBase(BaseModel):
    vendor_id: Optional[UUID] = Field(None, description="Vendor ID")
    material_id: Optional[UUID] = Field(None, description="Material ID")
    sku: Optional[str] = Field(None, description="SKU or product code")
    qty: float = Field(..., ge=0, description="Quantity purchased")
    unit: str = Field(..., description="Unit of measurement")
    unit_price_nis: float = Field(..., ge=0, description="Unit price in NIS")
    total_nis: float = Field(..., ge=0, description="Total price in NIS")
    currency: str = Field("NIS", description="Currency")
    tax_vat_pct: Optional[float] = Field(None, ge=0, le=100, description="VAT percentage")
    occurred_at: Optional[datetime] = Field(None, description="When the purchase occurred")
    receipt_path: Optional[str] = Field(None, description="Path to receipt file")

class PurchaseCreate(PurchaseBase):
    pass

class PurchaseUpdate(PurchaseBase):
    pass

class Purchase(PurchaseBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShippingQuoteBase(BaseModel):
    route_hash: Optional[str] = Field(None, description="Hash of route parameters")
    distance_km: Optional[float] = Field(None, ge=0, description="Distance in kilometers")
    weight_kg: Optional[float] = Field(None, ge=0, description="Weight in kilograms")
    type: Optional[str] = Field(None, description="Shipping type (standard/express/freight)")
    base_fee_nis: Optional[float] = Field(None, ge=0, description="Base fee in NIS")
    per_km_nis: Optional[float] = Field(None, ge=0, description="Cost per km in NIS")
    per_kg_nis: Optional[float] = Field(None, ge=0, description="Cost per kg in NIS")
    surge_json: Optional[dict] = Field(None, description="Surge pricing data")
    fetched_at: Optional[datetime] = Field(None, description="When the quote was fetched")
    source: Optional[str] = Field(None, description="Source of the quote")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence level")

class ShippingQuoteCreate(ShippingQuoteBase):
    pass

class ShippingQuoteUpdate(ShippingQuoteBase):
    pass

class ShippingQuote(ShippingQuoteBase):
    id: UUID
    
    class Config:
        from_attributes = True

class RateCardBase(BaseModel):
    role: str = Field(..., description="Labor role")
    hourly_rate_nis: float = Field(..., ge=0, description="Hourly rate in NIS")
    overtime_rules_json: Optional[dict] = Field(None, description="Overtime rules")
    default_efficiency: float = Field(1.0, ge=0, le=2, description="Default efficiency multiplier")

class RateCardCreate(RateCardBase):
    pass

class RateCardUpdate(RateCardBase):
    pass

class RateCard(RateCardBase):
    
    class Config:
        from_attributes = True