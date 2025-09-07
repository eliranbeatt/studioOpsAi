# Shared Packages Component

## 📦 Overview

The **Shared Packages** component provides common libraries, utilities, and data schemas that are used across multiple components of StudioOps AI. It ensures consistency, reduces code duplication, and provides centralized data validation and database utilities.

### Purpose and Role in StudioOps AI

The Shared Packages serve as the **common foundation layer** that:
- Provides consistent data schemas and validation across components
- Offers database utilities and connection management
- Ensures type safety through shared Pydantic models
- Facilitates code reuse and maintainability
- Standardizes data structures and interfaces

## 🏗️ Architecture Overview

```mermaid
graph TB
    API[🔌 API Backend] --> Packages[📦 Shared Packages]
    Services[🛠️ Services] --> Packages
    Tests[🧪 Tests] --> Packages
    
    Packages --> DB[🗄️ Database Package]
    Packages --> Schemas[📋 Schemas Package]
    
    DB --> DBUtils[🔧 Database Utilities]
    DB --> Connections[🔗 Connection Management]
    DB --> Seeding[🌱 Data Seeding]
    
    Schemas --> Projects[📋 Project Schemas]
    Schemas --> Auth[🔐 Auth Schemas]
    Schemas --> Estimation[💰 Estimation Schemas]
    Schemas --> Models[📊 Data Models]
```

## 🗄️ Database Package (`packages/db/`)

### **Database Connection Management**

```python
# packages/db/connection.py
"""Centralized database connection and session management"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator

# Base class for all models
Base = declarative_base()

class DatabaseManager:
    """Centralized database management"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'postgresql://studioops:studioops123@localhost:5432/studioops'
        )
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables"""
        Base.metadata.drop_all(bind=self.engine)

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    with db_manager.session_scope() as session:
        yield session
```

### **Database Utilities**

```python
# packages/db/utils.py
"""Database utility functions"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Collection of database utility functions"""
    
    @staticmethod
    def execute_raw_sql(session: Session, sql: str, params: Dict = None) -> List[Dict]:
        """Execute raw SQL and return results as dictionaries"""
        try:
            result = session.execute(text(sql), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Raw SQL execution failed: {e}")
            raise
    
    @staticmethod
    def bulk_insert(session: Session, model_class, data: List[Dict]) -> bool:
        """Perform bulk insert operation"""
        try:
            session.bulk_insert_mappings(model_class, data)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk insert failed: {e}")
            return False
    
    @staticmethod
    def get_table_info(session: Session, table_name: str) -> Dict:
        """Get table information including column details"""
        sql = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """
        return DatabaseUtils.execute_raw_sql(session, sql, {"table_name": table_name})
    
    @staticmethod
    def check_table_exists(session: Session, table_name: str) -> bool:
        """Check if a table exists in the database"""
        sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = :table_name
            )
        """
        result = DatabaseUtils.execute_raw_sql(session, sql, {"table_name": table_name})
        return result[0]['exists'] if result else False
    
    @staticmethod
    def get_database_stats(session: Session) -> Dict:
        """Get database statistics"""
        stats = {}
        
        # Table sizes
        sql = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public'
        """
        stats['table_stats'] = DatabaseUtils.execute_raw_sql(session, sql)
        
        # Database size
        sql = "SELECT pg_size_pretty(pg_database_size(current_database())) as size"
        result = DatabaseUtils.execute_raw_sql(session, sql)
        stats['database_size'] = result[0]['size'] if result else 'Unknown'
        
        return stats
```

### **Data Seeding**

```python
# packages/db/seed.py
"""Database seeding for development and testing"""

import json
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from ..schemas.projects import ProjectCreate, PlanCreate, PlanItemCreate
from ..schemas.auth import UserCreate
from .connection import db_manager

class DataSeeder:
    """Handles database seeding operations"""
    
    def __init__(self):
        self.session = db_manager.get_session()
    
    def seed_all(self):
        """Seed all data for development environment"""
        print("🌱 Starting database seeding...")
        
        try:
            self.seed_users()
            self.seed_vendors()
            self.seed_materials()
            self.seed_projects()
            self.seed_rate_cards()
            self.seed_sample_data()
            
            print("✅ Database seeding completed successfully!")
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()
    
    def seed_users(self):
        """Seed default users"""
        users_data = [
            {
                "username": "admin",
                "email": "admin@studioops.ai",
                "full_name": "System Administrator",
                "is_active": True,
                "is_superuser": True
            },
            {
                "username": "demo",
                "email": "demo@studioops.ai", 
                "full_name": "Demo User",
                "is_active": True,
                "is_superuser": False
            }
        ]
        
        for user_data in users_data:
            # Check if user exists
            existing = self.session.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(**user_data)
                user.hashed_password = get_password_hash("demo123")  # Default password
                self.session.add(user)
        
        self.session.commit()
        print("👥 Users seeded")
    
    def seed_vendors(self):
        """Seed sample vendors"""
        vendors_data = [
            {
                "name": "BuildMart",
                "contact": {"phone": "03-1234567", "email": "orders@buildmart.co.il"},
                "url": "https://buildmart.co.il",
                "rating": 4,
                "notes": "Reliable construction materials supplier"
            },
            {
                "name": "Wood & Style",
                "contact": {"phone": "08-9876543", "email": "info@woodstyle.co.il"},
                "url": "https://woodstyle.co.il",
                "rating": 5,
                "notes": "Premium wood and furniture materials"
            }
        ]
        
        for vendor_data in vendors_data:
            existing = self.session.query(Vendor).filter(Vendor.name == vendor_data["name"]).first()
            if not existing:
                vendor = Vendor(**vendor_data)
                self.session.add(vendor)
        
        self.session.commit()
        print("🏪 Vendors seeded")
    
    def seed_materials(self):
        """Seed sample materials"""
        materials_data = [
            {
                "name": "Pine Wood Board",
                "spec": "18mm Pine wood board, 122x244cm",
                "unit": "m²",
                "category": "wood",
                "typical_waste_pct": Decimal("0.10"),
                "notes": "Standard construction grade pine"
            },
            {
                "name": "Interior Paint",
                "spec": "White interior wall paint, premium grade",
                "unit": "liter",
                "category": "paint",
                "typical_waste_pct": Decimal("0.05"),
                "notes": "Covers approximately 10m² per liter"
            }
        ]
        
        for material_data in materials_data:
            existing = self.session.query(Material).filter(Material.name == material_data["name"]).first()
            if not existing:
                material = Material(**material_data)
                self.session.add(material)
        
        self.session.commit()
        print("🔨 Materials seeded")
    
    def seed_projects(self):
        """Seed sample projects with plans"""
        projects_data = [
            {
                "name": "Modern Kitchen Renovation",
                "client_name": "Cohen Family",
                "status": "active",
                "start_date": date(2024, 1, 15),
                "due_date": date(2024, 3, 15),
                "budget_planned": Decimal("50000.00")
            },
            {
                "name": "Office Space Design",
                "client_name": "TechStart Ltd",
                "status": "planning",
                "start_date": date(2024, 2, 1),
                "due_date": date(2024, 4, 1),
                "budget_planned": Decimal("75000.00")
            }
        ]
        
        for project_data in projects_data:
            existing = self.session.query(Project).filter(Project.name == project_data["name"]).first()
            if not existing:
                project = Project(**project_data)
                self.session.add(project)
                self.session.flush()  # Get the ID
                
                # Add sample plan
                plan = Plan(
                    project_id=str(project.id),
                    version=1,
                    status="draft",
                    margin_target=Decimal("0.25"),
                    currency="NIS"
                )
                self.session.add(plan)
        
        self.session.commit()
        print("📋 Projects seeded")
    
    def seed_rate_cards(self):
        """Seed labor rate cards"""
        rate_cards_data = [
            {"role": "carpenter", "hourly_rate_nis": Decimal("120.00"), "default_efficiency": Decimal("0.90")},
            {"role": "painter", "hourly_rate_nis": Decimal("100.00"), "default_efficiency": Decimal("0.85")},
            {"role": "electrician", "hourly_rate_nis": Decimal("150.00"), "default_efficiency": Decimal("0.85")},
            {"role": "plumber", "hourly_rate_nis": Decimal("140.00"), "default_efficiency": Decimal("0.85")},
            {"role": "laborer", "hourly_rate_nis": Decimal("80.00"), "default_efficiency": Decimal("1.00")},
            {"role": "project_manager", "hourly_rate_nis": Decimal("200.00"), "default_efficiency": Decimal("0.95")}
        ]
        
        for rate_data in rate_cards_data:
            existing = self.session.query(RateCard).filter(RateCard.role == rate_data["role"]).first()
            if not existing:
                rate_card = RateCard(**rate_data)
                self.session.add(rate_card)
        
        self.session.commit()
        print("💰 Rate cards seeded")

def main():
    """Main seeding function"""
    seeder = DataSeeder()
    seeder.seed_all()

if __name__ == "__main__":
    main()
```

## 📋 Schemas Package (`packages/schemas/`)

### **Project Schemas**

```python
# packages/schemas/projects.py
"""Pydantic schemas for project-related data"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

class ProjectBase(BaseModel):
    """Base project schema"""
    name: str = Field(..., min_length=1, max_length=255)
    client_name: Optional[str] = Field(None, max_length=255)
    status: str = Field(default="draft", regex="^(draft|planning|active|completed|archived|cancelled)$")
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    budget_planned: Optional[Decimal] = Field(None, ge=0)
    budget_actual: Optional[Decimal] = Field(None, ge=0)
    board_id: Optional[str] = None

class ProjectCreate(ProjectBase):
    """Schema for creating a project"""
    pass

class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    client_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, regex="^(draft|planning|active|completed|archived|cancelled)$")
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    budget_planned: Optional[Decimal] = Field(None, ge=0)
    budget_actual: Optional[Decimal] = Field(None, ge=0)

class Project(ProjectBase):
    """Complete project schema with database fields"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PlanItemBase(BaseModel):
    """Base plan item schema"""
    category: str = Field(..., regex="^(materials|labor|tools|logistics|other)$")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    vendor_id: Optional[str] = None
    labor_role: Optional[str] = None
    labor_hours: Optional[Decimal] = Field(None, ge=0)
    lead_time_days: Optional[Decimal] = Field(None, ge=0)
    risk_level: Optional[str] = Field(None, regex="^(low|medium|high)$")
    notes: Optional[str] = None

class PlanItemCreate(PlanItemBase):
    """Schema for creating a plan item"""
    plan_id: str

class PlanItem(PlanItemBase):
    """Complete plan item schema"""
    id: str
    plan_id: str
    subtotal: Optional[Decimal] = None
    unit_price_source: Optional[Dict[str, Any]] = None
    dependency_ids: Optional[List[str]] = None
    attrs: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class PlanBase(BaseModel):
    """Base plan schema"""
    project_id: str
    version: int = Field(..., ge=1)
    status: str = Field(default="draft", regex="^(draft|approved|archived)$")
    margin_target: Decimal = Field(default=Decimal("0.25"), ge=0, le=1)
    currency: str = Field(default="NIS", regex="^(NIS|USD|EUR)$")

class PlanCreate(PlanBase):
    """Schema for creating a plan"""
    pass

class Plan(PlanBase):
    """Complete plan schema"""
    id: str
    items: List[PlanItem] = []
    total_cost: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        
    @validator('total_cost', always=True)
    def calculate_total(cls, v, values):
        """Calculate total cost from items"""
        if 'items' in values and values['items']:
            return sum(item.subtotal or 0 for item in values['items'])
        return v
```

### **Authentication Schemas**

```python
# packages/schemas/auth.py
"""Authentication and user management schemas"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Schema for user updates"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class User(UserBase):
    """Complete user schema"""
    id: str
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """JWT token schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: List[str] = []

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
```

### **Estimation Schemas**

```python
# packages/schemas/estimation.py
"""Cost estimation related schemas"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum
from datetime import date

class ShippingMethod(str, Enum):
    """Shipping method options"""
    STANDARD = "standard"
    EXPRESS = "express"
    FREIGHT = "freight"
    LOCAL = "local"

class LaborRole(str, Enum):
    """Labor role options"""
    CARPENTER = "carpenter"
    PAINTER = "painter"
    ELECTRICIAN = "electrician"
    PLUMBER = "plumber"
    LABORER = "laborer"
    PROJECT_MANAGER = "project_manager"
    DESIGNER = "designer"
    INSTALLER = "installer"

class ShippingEstimateRequest(BaseModel):
    """Request schema for shipping cost estimation"""
    distance_km: Decimal = Field(..., gt=0, description="Distance in kilometers")
    weight_kg: Decimal = Field(..., gt=0, description="Weight in kilograms")
    method: ShippingMethod = Field(..., description="Shipping method")
    urgency: Decimal = Field(default=Decimal("1.0"), ge=1.0, le=3.0, description="Urgency multiplier")
    fragile: bool = Field(default=False, description="Whether items are fragile")
    insurance_value: Optional[Decimal] = Field(None, ge=0, description="Insurance value in NIS")

class ShippingEstimate(BaseModel):
    """Shipping cost estimation result"""
    base_cost: Decimal
    distance_cost: Decimal
    weight_cost: Decimal
    urgency_surcharge: Decimal = Decimal("0.0")
    fragile_surcharge: Decimal = Decimal("0.0")
    insurance_cost: Decimal = Decimal("0.0")
    total_cost: Decimal
    confidence: Decimal = Field(..., ge=0.0, le=1.0)
    estimated_days: Decimal
    method: ShippingMethod
    notes: Optional[str] = None

class LaborEstimateRequest(BaseModel):
    """Request schema for labor cost estimation"""
    role: LaborRole
    hours: Decimal = Field(..., gt=0, description="Estimated hours")
    complexity: Decimal = Field(default=Decimal("1.0"), ge=0.5, le=2.0, description="Complexity multiplier")
    efficiency: Optional[Decimal] = Field(None, ge=0.1, le=1.5, description="Worker efficiency")
    overtime: bool = Field(default=False, description="Whether overtime rates apply")

class LaborEstimate(BaseModel):
    """Labor cost estimation result"""
    role: LaborRole
    hours: Decimal
    base_hourly_rate: Decimal
    effective_hourly_rate: Decimal
    total_cost: Decimal
    complexity_factor: Decimal
    efficiency_factor: Decimal
    overtime_premium: Decimal = Decimal("0.0")
    confidence: Decimal = Field(..., ge=0.0, le=1.0)

class MaterialRequirement(BaseModel):
    """Material requirement for project estimation"""
    material_id: Optional[str] = None
    name: str
    quantity: Decimal = Field(..., gt=0)
    unit: str
    estimated_unit_price: Optional[Decimal] = None
    waste_factor: Decimal = Field(default=Decimal("0.1"), ge=0.0, le=1.0)
    lead_time_days: Optional[Decimal] = None

class ProjectEstimateRequest(BaseModel):
    """Request schema for complete project estimation"""
    project_name: str
    materials: List[MaterialRequirement] = []
    labor_requirements: List[LaborEstimateRequest] = []
    shipping_distance: Optional[Decimal] = None
    project_complexity: Decimal = Field(default=Decimal("1.0"), ge=0.5, le=3.0)
    timeline_pressure: Decimal = Field(default=Decimal("1.0"), ge=0.5, le=2.0)
    margin_target: Decimal = Field(default=Decimal("0.25"), ge=0.0, le=1.0)

class ProjectEstimate(BaseModel):
    """Complete project cost estimation"""
    project_name: str
    materials_cost: Decimal
    labor_cost: Decimal
    shipping_cost: Decimal
    subtotal: Decimal
    margin_amount: Decimal
    total_cost: Decimal
    confidence: Decimal = Field(..., ge=0.0, le=1.0)
    estimated_timeline_days: Optional[Decimal] = None
    breakdown: Dict[str, Any] = {}
    notes: List[str] = []
    
    @validator('total_cost', always=True)
    def calculate_total(cls, v, values):
        """Calculate total cost including margin"""
        if all(k in values for k in ['subtotal', 'margin_amount']):
            return values['subtotal'] + values['margin_amount']
        return v

class RateCardUpdate(BaseModel):
    """Schema for updating labor rate cards"""
    role: LaborRole
    hourly_rate_nis: Decimal = Field(..., gt=0)
    overtime_rules: Optional[Dict[str, Any]] = None
    default_efficiency: Decimal = Field(default=Decimal("1.0"), ge=0.1, le=2.0)
```

## 🔧 Shared Utilities

### **Common Validators**

```python
# packages/schemas/validators.py
"""Common validation utilities"""

from pydantic import validator, Field
from typing import Any, Dict, List
from decimal import Decimal
import re

class BaseValidators:
    """Common validators for use across schemas"""
    
    @staticmethod
    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None"""
        if isinstance(v, str) and v.strip() == '':
            return None
        return v
    
    @staticmethod
    def validate_positive_decimal(v):
        """Validate positive decimal values"""
        if v is not None and v <= 0:
            raise ValueError('Value must be positive')
        return v
    
    @staticmethod
    def validate_percentage(v):
        """Validate percentage values (0-1)"""
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Percentage must be between 0 and 1')
        return v
    
    @staticmethod
    def validate_phone_number(v):
        """Validate Israeli phone number format"""
        if v is not None:
            # Remove spaces and dashes
            cleaned = re.sub(r'[\s-]', '', v)
            # Check Israeli phone number patterns
            if not re.match(r'^(\+972|0)(5[0-9]|7[2-9]|8[6-9]|9[6-9]|2|3|4|8)[0-9]{7}$', cleaned):
                raise ValueError('Invalid Israeli phone number format')
        return v
    
    @staticmethod
    def validate_email_list(v):
        """Validate list of email addresses"""
        if isinstance(v, list):
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            for email in v:
                if not re.match(email_pattern, email):
                    raise ValueError(f'Invalid email address: {email}')
        return v
```

## 🎯 Package Integration

### **API Backend Integration**

```python
# Example usage in API routers
from packages.schemas.projects import ProjectCreate, Project
from packages.db.connection import get_db

@router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project using shared schemas"""
    db_project = ProjectModel(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
```

### **Testing Integration**

```python
# Example usage in tests
from packages.schemas.projects import ProjectCreate
from packages.db.seed import DataSeeder

def test_project_creation():
    """Test project creation with shared schemas"""
    project_data = ProjectCreate(
        name="Test Project",
        client_name="Test Client",
        status="draft"
    )
    
    # Validate data through Pydantic schema
    assert project_data.name == "Test Project"
    assert project_data.status == "draft"
```

## 📋 Benefits and Usage

### **Consistency Across Components**
- **Unified Data Models**: Same schemas used in API, tests, and services
- **Type Safety**: TypeScript-like validation in Python
- **Documentation**: Automatic API documentation generation
- **Validation**: Centralized validation rules and error messages

### **Development Efficiency**
- **Code Reuse**: Reduced duplication across components  
- **Maintainability**: Single source of truth for data structures
- **Testing**: Consistent test data and validation
- **API Documentation**: Automatic OpenAPI schema generation

### **Quality Assurance**
- **Data Integrity**: Consistent validation across all entry points
- **Error Prevention**: Early validation prevents runtime errors
- **Documentation**: Self-documenting code through schema definitions
- **Testing**: Standardized test fixtures and data generation

The Shared Packages component provides the essential foundation for data consistency, type safety, and code reuse across the entire StudioOps AI system, ensuring reliable and maintainable code architecture.