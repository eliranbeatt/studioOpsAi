"""Pydantic models for projects and plans"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class ProjectBase(BaseModel):
    name: str = Field(..., description="Project name")
    client_name: Optional[str] = Field(None, description="Client name")
    status: Optional[str] = Field("draft", description="Project status")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    due_date: Optional[datetime] = Field(None, description="Project due date")
    budget_planned: Optional[float] = Field(None, description="Planned budget")
    budget_actual: Optional[float] = Field(None, description="Actual budget")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    name: Optional[str] = Field(None, description="Project name")

class Project(ProjectBase):
    id: UUID
    board_id: Optional[str] = Field(None, description="Trello board ID")
    created_at: datetime
    updated_at: Optional[datetime] = Field(None, description="Last updated timestamp")

    class Config:
        from_attributes = True

class PlanItemBase(BaseModel):
    category: str = Field(..., description="Item category")
    title: str = Field(..., description="Item title")
    description: Optional[str] = Field(None, description="Item description")
    quantity: float = Field(1.0, description="Quantity")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    unit_price: Optional[float] = Field(None, description="Unit price")
    unit_price_source: Optional[Dict[str, Any]] = Field(None, description="Price source info")
    vendor_id: Optional[UUID] = Field(None, description="Vendor ID")
    labor_role: Optional[str] = Field(None, description="Labor role")
    labor_hours: Optional[float] = Field(None, description="Labor hours")
    lead_time_days: Optional[float] = Field(None, description="Lead time in days")
    dependency_ids: Optional[List[str]] = Field(None, description="Dependency IDs")
    risk_level: Optional[str] = Field(None, description="Risk level")
    notes: Optional[str] = Field(None, description="Notes")

class PlanItemCreate(PlanItemBase):
    pass

class PlanItemUpdate(PlanItemBase):
    category: Optional[str] = Field(None, description="Item category")
    title: Optional[str] = Field(None, description="Item title")
    quantity: Optional[float] = Field(None, description="Quantity")

class PlanItem(PlanItemBase):
    id: UUID
    subtotal: Optional[float] = Field(None, description="Subtotal amount")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlanBase(BaseModel):
    margin_target: float = Field(0.25, description="Target margin")
    currency: str = Field("NIS", description="Currency")

class PlanCreate(PlanBase):
    project_id: UUID = Field(..., description="Project ID")
    version: int = Field(1, description="Plan version")

class PlanUpdate(PlanBase):
    status: Optional[str] = Field(None, description="Plan status")
    margin_target: Optional[float] = Field(None, description="Target margin")

class Plan(PlanBase):
    id: UUID
    project_id: UUID
    version: int
    status: str = Field("draft", description="Plan status")
    items: List[PlanItem] = Field(default_factory=list, description="Plan items")
    total: float = Field(0.0, description="Total amount")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    type: str = Field(..., description="Document type")
    path: str = Field(..., description="Document path")
    version: int = Field(1, description="Document version")

class DocumentCreate(DocumentBase):
    project_id: UUID = Field(..., description="Project ID")
    snapshot_jsonb: Optional[Dict[str, Any]] = Field(None, description="Document snapshot")

class DocumentUpdate(DocumentBase):
    type: Optional[str] = Field(None, description="Document type")
    path: Optional[str] = Field(None, description="Document path")

class Document(DocumentBase):
    id: UUID
    project_id: UUID
    snapshot_jsonb: Optional[Dict[str, Any]] = Field(None, description="Document snapshot")
    created_by: Optional[str] = Field(None, description="Created by")
    created_at: datetime

    class Config:
        from_attributes = True