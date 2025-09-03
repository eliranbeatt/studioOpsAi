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