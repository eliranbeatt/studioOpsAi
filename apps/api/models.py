"""Database models for StudioOps AI"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, Date, Numeric, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
import uuid

Base = declarative_base()

def generate_ulid():
    return str(uuid.uuid4())

class ChatMessage(Base):
    """Chat message storage for memory"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    session_id = Column(String, index=True, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)
    project_context = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ChatMessage(session_id={self.session_id}, message={self.message[:50]}...)>"

class ChatSession(Base):
    """Chat session management"""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    user_id = Column(String, index=True, nullable=True)
    project_id = Column(String, index=True, nullable=True)
    title = Column(String, nullable=True)
    context = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title})>"

class RAGDocument(Base):
    """RAG document storage"""
    __tablename__ = "rag_documents"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=True)  # e.g., 'manual', 'upload', 'web'
    document_type = Column(String, nullable=True)  # e.g., 'spec', 'manual', 'guide'
    meta_data = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)  # Store vector embeddings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RAGDocument(title={self.title}, type={self.document_type})>"

class ProjectKnowledge(Base):
    """Project-specific knowledge base"""
    __tablename__ = "project_knowledge"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    project_id = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)  # e.g., 'materials', 'techniques', 'pricing'
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProjectKnowledge(project={self.project_id}, key={self.key})>"

class Project(Base):
    """Project management"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    name = Column(String, nullable=False)
    client_name = Column(String, nullable=True)
    board_id = Column(String, nullable=True)  # Trello board ID
    status = Column(String, default="draft")
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    budget_planned = Column(Numeric(14, 2), nullable=True)
    budget_actual = Column(Numeric(14, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Project(name={self.name}, client={self.client_name})>"

class Plan(Base):
    """Project plans with versioning"""
    __tablename__ = "plans"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    project_id = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    status = Column(String, default="draft")  # draft, approved, archived
    margin_target = Column(Numeric(4, 3), default=0.25)
    currency = Column(String, default="NIS")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Plan(project={self.project_id}, version={self.version})>"

class PlanItem(Base):
    """Plan line items"""
    __tablename__ = "plan_items"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    plan_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Numeric(14, 3), default=1)
    unit = Column(String, nullable=True)
    unit_price = Column(Numeric(14, 2), nullable=True)
    unit_price_source = Column(JSON, nullable=True)
    vendor_id = Column(String, nullable=True)
    labor_role = Column(String, nullable=True)
    labor_hours = Column(Numeric(10, 2), nullable=True)
    lead_time_days = Column(Numeric(6, 2), nullable=True)
    dependency_ids = Column(JSON, nullable=True)
    risk_level = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    subtotal = Column(Numeric(14, 2), nullable=True)
    attrs = Column(JSON, nullable=True)
    item_metadata = Column("metadata", JSON, nullable=True)
    
    def __repr__(self):
        return f"<PlanItem(title={self.title}, category={self.category})>"

class Vendor(Base):
    """Vendor information"""
    __tablename__ = "vendors"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    name = Column(String, nullable=False)
    contact = Column(JSON, nullable=True)
    url = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Vendor(name={self.name})>"

class Material(Base):
    """Material specifications"""
    __tablename__ = "materials"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    name = Column(String, nullable=False)
    spec = Column(Text, nullable=True)
    unit = Column(String, nullable=False)
    category = Column(String, nullable=True)
    typical_waste_pct = Column(Numeric(5, 2), default=0)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Material(name={self.name}, unit={self.unit})>"

class VendorPrice(Base):
    """Vendor pricing information"""
    __tablename__ = "vendor_prices"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    vendor_id = Column(String, nullable=True)
    material_id = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    price_nis = Column(Numeric(14, 2), nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)
    source_url = Column(String, nullable=True)
    confidence = Column(Numeric(3, 2), default=0.8)
    is_quote = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<VendorPrice(price={self.price_nis}, confidence={self.confidence})>"

class Purchase(Base):
    """Purchase history"""
    __tablename__ = "purchases"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    vendor_id = Column(String, nullable=True)
    material_id = Column(String, nullable=True)
    project_id = Column(String, nullable=True)
    qty = Column(Numeric(14, 3), nullable=True)
    unit_price_nis = Column(Numeric(14, 2), nullable=True)
    tax_vat_pct = Column(Numeric(5, 2), nullable=True)
    occurred_at = Column(Date, nullable=True)
    receipt_path = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Purchase(qty={self.qty}, price={self.unit_price_nis})>"

class ShippingQuote(Base):
    """Shipping quotes and estimates"""
    __tablename__ = "shipping_quotes"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    route_hash = Column(String, nullable=True)
    distance_km = Column(Numeric(10, 2), nullable=True)
    weight_kg = Column(Numeric(10, 2), nullable=True)
    type = Column(String, nullable=True)
    base_fee_nis = Column(Numeric(14, 2), nullable=True)
    per_km_nis = Column(Numeric(10, 2), nullable=True)
    per_kg_nis = Column(Numeric(10, 2), nullable=True)
    surge_json = Column(JSON, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String, nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    
    def __repr__(self):
        return f"<ShippingQuote(base={self.base_fee_nis}, confidence={self.confidence})>"

class RateCard(Base):
    """Labor rate cards"""
    __tablename__ = "rate_cards"
    
    role = Column(String, primary_key=True)
    hourly_rate_nis = Column(Numeric(10, 2), nullable=False)
    overtime_rules_json = Column(JSON, nullable=True)
    default_efficiency = Column(Numeric(3, 2), default=1.0)
    
    def __repr__(self):
        return f"<RateCard(role={self.role}, rate={self.hourly_rate_nis})>"

class Document(Base):
    """Document repository"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    language = Column(String, nullable=True)  # he/en
    type = Column(String, nullable=True)  # quote|project_brief|invoice|receipt|shipping_quote|catalog|trello_export|other
    confidence = Column(Numeric(3, 2), nullable=True)
    project_id = Column(String, nullable=True)
    storage_path = Column(String, nullable=False)
    content_sha256 = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Document(filename={self.filename}, type={self.type})>"

class DocChunk(Base):
    """Document chunks for FTS"""
    __tablename__ = "doc_chunks"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    document_id = Column(String, nullable=False)
    page = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    # tsv column would be added via migration for FTS
    
    def __repr__(self):
        return f"<DocChunk(document={self.document_id}, page={self.page})>"

class ExtractedItem(Base):
    """Extracted items from ingestion"""
    __tablename__ = "extracted_items"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    document_id = Column(String, nullable=False)
    project_id = Column(String, nullable=True)
    type = Column(String, nullable=False)  # line_item|purchase|shipping|decision|metadata
    vendor_id = Column(String, nullable=True)
    material_id = Column(String, nullable=True)
    title = Column(String, nullable=True)
    qty = Column(Numeric(14, 3), nullable=True)
    unit = Column(String, nullable=True)
    unit_price_nis = Column(Numeric(14, 2), nullable=True)
    vat_pct = Column(Numeric(5, 2), nullable=True)
    lead_time_days = Column(Numeric(6, 2), nullable=True)
    attrs = Column(JSON, nullable=True)
    source_ref = Column(String, nullable=False)  # doc:page:span
    evidence = Column(Text, nullable=True)
    confidence = Column(Numeric(3, 2), default=0.8)
    occurred_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ExtractedItem(type={self.type}, confidence={self.confidence})>"

class VendorAlias(Base):
    """Vendor name aliases"""
    __tablename__ = "vendor_aliases"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    vendor_id = Column(String, nullable=False)
    alias = Column(String, nullable=False)
    source_ref = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<VendorAlias(vendor={self.vendor_id}, alias={self.alias})>"

class MaterialAlias(Base):
    """Material name aliases"""
    __tablename__ = "material_aliases"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    material_id = Column(String, nullable=False)
    alias = Column(String, nullable=False)
    source_ref = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<MaterialAlias(material={self.material_id}, alias={self.alias})>"

class IngestEvent(Base):
    """Ingestion pipeline events"""
    __tablename__ = "ingest_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False)
    stage = Column(String, nullable=False)  # upload|parse|classify|pack|extract|validate|link|stage|clarify|commit|error
    status = Column(String, nullable=False)  # start|ok|retry|fail
    payload_jsonb = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<IngestEvent(stage={self.stage}, status={self.status})>"

class GeneratedDocument(Base):
    """Generated documents"""
    __tablename__ = "generated_documents"
    
    id = Column(String, primary_key=True, default=generate_ulid)
    project_id = Column(String, nullable=True)
    type = Column(String, nullable=False)  # quote|planning
    path_pdf = Column(String, nullable=False)
    snapshot_jsonb = Column(JSON, nullable=True)
    version = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<GeneratedDocument(type={self.type}, project={self.project_id})>"