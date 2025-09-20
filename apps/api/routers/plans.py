from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
import json

from database import get_db
from models import Plan as PlanModel, PlanItem as PlanItemModel
from packages.schemas.projects import Plan, PlanCreate, PlanUpdate, PlanItem, PlanItemCreate
from services.pricing_resolver import pricing_resolver

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanGenerateRequest(BaseModel):
    project_id: Optional[str] = None
    project_name: str
    goal: Optional[str] = None
    project_description: Optional[str] = None

class GeneratedPlan(BaseModel):
    project_id: Optional[str]
    project_name: str
    items: List[Dict[str, Any]]
    total: float
    margin_target: float
    currency: str
    metadata: Dict[str, Any]

@router.post("/generate", response_model=GeneratedPlan)
async def generate_plan(payload: PlanGenerateRequest):
    """Generate a structured plan JSON from a goal/description without persisting it."""
    try:
        name = payload.project_name or "New Project"
        desc = payload.project_description or payload.goal or ""

        # Basic heuristic to select materials
        if desc:
            lowered = desc.lower()
        else:
            lowered = ""

        if any(k in lowered for k in ["cabinet", "furniture"]):
            materials = ["Plywood 4x8", "2x4 Lumber", "Screws"]
        elif "painting" in lowered:
            materials = ["Paint"]
        else:
            materials = ["Plywood 4x8", "2x4 Lumber", "Screws", "Nails"]

        items: List[Dict[str, Any]] = []
        total = 0.0

        # Materials with pricing
        for mat in materials:
            price = pricing_resolver.get_material_price(mat)
            if price:
                qty = _estimate_material_quantity_for_plans(mat, lowered)
                sub = qty * price["price"]
                items.append({
                    "category": "materials",
                    "title": price["material_name"],
                    "description": f"{mat} from {price['vendor_name']}",
                    "quantity": qty,
                    "unit": price["unit"],
                    "unit_price": price["price"],
                    "unit_price_source": {
                        "vendor": price["vendor_name"],
                        "confidence": price["confidence"],
                        "fetched_at": price["fetched_at"].isoformat() if price.get("fetched_at") else None,
                    },
                    "subtotal": round(sub, 2),
                })
                total += sub

        # Labor roles
        roles = ["Carpenter"]
        if "painting" in lowered:
            roles.append("Painter")
        if "electrical" in lowered:
            roles.append("Electrician")

        for role in roles:
            labor = pricing_resolver.get_labor_rate(role)
            if labor:
                hours = _estimate_labor_hours_for_plans(role, lowered, len(materials))
                sub = hours * labor["hourly_rate"]
                items.append({
                    "category": "labor",
                    "title": f"{role} work",
                    "description": f"{role} services for {name}",
                    "quantity": hours,
                    "unit": "hour",
                    "unit_price": labor["hourly_rate"],
                    "labor_role": role,
                    "labor_hours": hours,
                    "subtotal": round(sub, 2),
                })
                total += sub

        # Logistics
        shipping = pricing_resolver.estimate_shipping_cost(100, 50)
        items.append({
            "category": "logistics",
            "title": "Shipping & Delivery",
            "description": "Material delivery and logistics",
            "quantity": 1,
            "unit": "delivery",
            "unit_price": shipping["estimated_cost"],
            "subtotal": round(shipping["estimated_cost"], 2),
        })
        total += shipping["estimated_cost"]

        return {
            "project_id": payload.project_id,
            "project_name": name,
            "items": items,
            "total": round(total, 2),
            "margin_target": 0.25,
            "currency": "NIS",
            "metadata": {
                "generated_via": "plans.generate",
                "items_count": len(items),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {e}")


def _estimate_material_quantity_for_plans(material_name: str, lowered_desc: str) -> float:
    base = {
        "Plywood 4x8": 8.0,
        "2x4 Lumber": 20.0,
        "Screws": 2.0,
        "Nails": 1.0,
        "Paint": 3.0,
        "Drywall": 15.0,
    }
    qty = base.get(material_name, 1.0)
    if any(k in lowered_desc for k in ["large", "big"]):
        return qty * 1.5
    if any(k in lowered_desc for k in ["small", "simple"]):
        return qty * 0.7
    return qty

def _estimate_labor_hours_for_plans(role: str, lowered_desc: str, materials_count: int) -> float:
    base = {"Carpenter": 16.0, "Painter": 8.0, "Electrician": 6.0, "Laborer": 12.0}
    hours = base.get(role, 8.0)
    if any(k in lowered_desc for k in ["complex", "detailed"]):
        hours *= 1.5
    elif any(k in lowered_desc for k in ["simple", "basic"]):
        hours *= 0.8
    if materials_count > 5:
        hours *= 1.3
    elif materials_count < 2:
        hours *= 0.7
    return round(hours, 1)

@router.get("/project/{project_id}", response_model=List[Plan])
async def get_project_plans(project_id: UUID, db: Session = Depends(get_db)):
    """Get all plans for a project"""
    try:
        plans = db.query(PlanModel).filter(PlanModel.project_id == str(project_id)).order_by(PlanModel.version.desc()).all()
        
        result = []
        for plan in plans:
            plan_data = {
                "id": plan.id,
                "project_id": plan.project_id,
                "version": plan.version,
                "status": plan.status,
                "margin_target": float(plan.margin_target),
                "currency": plan.currency,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
                "items": [],
                "total": 0.0
            }
            
            # Get plan items
            items = db.query(PlanItemModel).filter(PlanItemModel.plan_id == plan.id).all()
            total = 0.0
            for item in items:
                item_data = {
                    "id": item.id,
                    "category": item.category,
                    "title": item.title,
                    "description": item.description,
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "unit_price": float(item.unit_price) if item.unit_price else None,
                    "unit_price_source": json.loads(item.unit_price_source) if item.unit_price_source else None,
                    "vendor_id": item.vendor_id,
                    "labor_role": item.labor_role,
                    "labor_hours": float(item.labor_hours) if item.labor_hours else None,
                    "lead_time_days": float(item.lead_time_days) if item.lead_time_days else None,
                    "dependency_ids": json.loads(item.dependency_ids) if item.dependency_ids else None,
                    "risk_level": item.risk_level,
                    "notes": item.notes,
                    "subtotal": float(item.subtotal) if item.subtotal else None,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                }
                plan_data["items"].append(item_data)
                if item.subtotal:
                    total += float(item.subtotal)
            
            plan_data["total"] = total
            result.append(plan_data)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching plans: {e}")

@router.get("/{plan_id}", response_model=Plan)
async def get_plan(plan_id: UUID, db: Session = Depends(get_db)):
    """Get a specific plan by ID"""
    try:
        plan = db.query(PlanModel).filter(PlanModel.id == str(plan_id)).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan_data = {
            "id": plan.id,
            "project_id": plan.project_id,
            "version": plan.version,
            "status": plan.status,
            "margin_target": float(plan.margin_target),
            "currency": plan.currency,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "items": [],
            "total": 0.0
        }
        
        # Get plan items
        items = db.query(PlanItemModel).filter(PlanItemModel.plan_id == plan.id).all()
        total = 0.0
        for item in items:
            item_data = {
                "id": item.id,
                "category": item.category,
                "title": item.title,
                "description": item.description,
                "quantity": float(item.quantity),
                "unit": item.unit,
                "unit_price": float(item.unit_price) if item.unit_price else None,
                "unit_price_source": json.loads(item.unit_price_source) if item.unit_price_source else None,
                "vendor_id": item.vendor_id,
                "labor_role": item.labor_role,
                "labor_hours": float(item.labor_hours) if item.labor_hours else None,
                "lead_time_days": float(item.lead_time_days) if item.lead_time_days else None,
                "dependency_ids": json.loads(item.dependency_ids) if item.dependency_ids else None,
                "risk_level": item.risk_level,
                "notes": item.notes,
                "subtotal": float(item.subtotal) if item.subtotal else None,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            }
            plan_data["items"].append(item_data)
            if item.subtotal:
                total += float(item.subtotal)
        
        plan_data["total"] = total
        
        return plan_data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching plan: {e}")

@router.post("/", response_model=Plan)
async def create_plan(plan: PlanCreate):
    """Create a new plan"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if project exists
        cursor.execute("SELECT id FROM projects WHERE id = %s", (str(plan.project_id),))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get next version number
        cursor.execute("""
            SELECT COALESCE(MAX(version), 0) + 1 FROM plans WHERE project_id = %s
        """, (str(plan.project_id),))
        next_version = cursor.fetchone()[0]
        
        # Create plan
        cursor.execute("""
            INSERT INTO plans (project_id, version, status, margin_target, currency)
            VALUES (%s, %s, 'draft', %s, %s)
            RETURNING id, created_at, updated_at
        """, (str(plan.project_id), next_version, plan.margin_target, plan.currency))
        
        result = cursor.fetchone()
        plan_id = result[0]
        
        conn.commit()
        
        # Return the created plan
        created_plan = {
            "id": plan_id,
            "project_id": plan.project_id,
            "version": next_version,
            "status": "draft",
            "margin_target": plan.margin_target,
            "currency": plan.currency,
            "items": [],
            "total": 0.0,
            "created_at": result[1],
            "updated_at": result[2]
        }
        
        cursor.close()
        conn.close()
        return created_plan
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating plan: {e}")

@router.put("/{plan_id}", response_model=Plan)
async def update_plan(plan_id: UUID, plan_update: PlanUpdate):
    """Update a plan"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = []
        update_values = []
        
        if plan_update.status is not None:
            update_fields.append("status = %s")
            update_values.append(plan_update.status)
        if plan_update.margin_target is not None:
            update_fields.append("margin_target = %s")
            update_values.append(plan_update.margin_target)
        if plan_update.currency is not None:
            update_fields.append("currency = %s")
            update_values.append(plan_update.currency)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_values.append(str(plan_id))
        
        query = f"""UPDATE plans SET {', '.join(update_fields)}, updated_at = NOW()
                   WHERE id = %s RETURNING project_id, version, created_at, updated_at"""
        
        cursor.execute(query, update_values)
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        conn.commit()
        
        # Get the updated plan
        cursor.execute("""
            SELECT status, margin_target, currency FROM plans WHERE id = %s
        """, (str(plan_id),))
        
        plan_data = cursor.fetchone()
        
        updated_plan = {
            "id": plan_id,
            "project_id": result[0],
            "version": result[1],
            "status": plan_data[0],
            "margin_target": float(plan_data[1]),
            "currency": plan_data[2],
            "items": [],
            "total": 0.0,
            "created_at": result[2],
            "updated_at": result[3]
        }
        
        # Get plan items
        cursor2 = conn.cursor()
        cursor2.execute("""
            SELECT id, category, title, description, quantity, unit, unit_price,
                   unit_price_source, vendor_id, labor_role, labor_hours,
                   lead_time_days, dependency_ids, risk_level, notes,
                   subtotal, created_at, updated_at
            FROM plan_items WHERE plan_id = %s
        """, (str(plan_id),))
        
        total = 0.0
        for item_row in cursor2.fetchall():
            item = {
                "id": item_row[0],
                "category": item_row[1],
                "title": item_row[2],
                "description": item_row[3],
                "quantity": float(item_row[4]),
                "unit": item_row[5],
                "unit_price": float(item_row[6]) if item_row[6] else None,
                "unit_price_source": json.loads(item_row[7]) if item_row[7] else None,
                "vendor_id": item_row[8],
                "labor_role": item_row[9],
                "labor_hours": float(item_row[10]) if item_row[10] else None,
                "lead_time_days": float(item_row[11]) if item_row[11] else None,
                "dependency_ids": json.loads(item_row[12]) if item_row[12] else None,
                "risk_level": item_row[13],
                "notes": item_row[14],
                "subtotal": float(item_row[15]) if item_row[15] else None,
                "created_at": item_row[16],
                "updated_at": item_row[17]
            }
            updated_plan["items"].append(item)
            if item_row[15]:
                total += float(item_row[15])
        
        cursor2.close()
        updated_plan["total"] = total
        
        cursor.close()
        conn.close()
        return updated_plan
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating plan: {e}")

@router.post("/{plan_id}/items", response_model=PlanItem)
async def add_plan_item(plan_id: UUID, item: PlanItemCreate):
    """Add an item to a plan"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if plan exists
        cursor.execute("SELECT id FROM plans WHERE id = %s", (str(plan_id),))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Auto-resolve price if not provided
        unit_price = item.unit_price
        unit_price_source = item.unit_price_source
        
        if unit_price is None and item.title:
            # Try to resolve price from vendor database
            price_data = pricing_resolver.get_material_price(item.title)
            if price_data:
                unit_price = price_data['price']
                unit_price_source = {
                    'source': 'vendor_database',
                    'vendor': price_data['vendor_name'],
                    'confidence': price_data['confidence'],
                    'fetched_at': price_data['fetched_at'].isoformat() if price_data['fetched_at'] else None,
                    'sku': price_data['sku']
                }
        
        # Calculate subtotal
        subtotal = item.quantity * (unit_price or 0)
        
        # Insert item
        cursor.execute("""
            INSERT INTO plan_items (
                plan_id, category, title, description, quantity, unit, unit_price,
                unit_price_source, vendor_id, labor_role, labor_hours,
                lead_time_days, dependency_ids, risk_level, notes, subtotal
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """, (
            str(plan_id), item.category, item.title, item.description,
            item.quantity, item.unit, unit_price,
            json.dumps(unit_price_source) if unit_price_source else None,
            str(item.vendor_id) if item.vendor_id else None,
            item.labor_role, item.labor_hours, item.lead_time_days,
            json.dumps(item.dependency_ids) if item.dependency_ids else None,
            item.risk_level, item.notes, subtotal
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        new_item = {
            "id": result[0],
            "category": item.category,
            "title": item.title,
            "description": item.description,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": unit_price,
            "unit_price_source": unit_price_source,
            "vendor_id": item.vendor_id,
            "labor_role": item.labor_role,
            "labor_hours": item.labor_hours,
            "lead_time_days": item.lead_time_days,
            "dependency_ids": item.dependency_ids,
            "risk_level": item.risk_level,
            "notes": item.notes,
            "subtotal": subtotal,
            "created_at": result[1],
            "updated_at": result[2]
        }
        
        cursor.close()
        conn.close()
        return new_item
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding plan item: {e}")

@router.delete("/{plan_id}/items/{item_id}")
async def delete_plan_item(plan_id: UUID, item_id: UUID):
    """Delete a plan item"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM plan_items WHERE id = %s AND plan_id = %s RETURNING id",
            (str(item_id), str(plan_id))
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Plan item not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Plan item deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting plan item: {e}")
