# API Backend Component

## 🔌 Overview

The **API Backend** is the core business logic and data management layer of StudioOps AI. Built with FastAPI and Python, it provides a comprehensive RESTful API that handles all business operations, AI integrations, and data persistence.

### Purpose and Role in StudioOps AI

The API Backend serves as the **central nervous system** that:
- Manages all business data through comprehensive ORM models
- Provides RESTful endpoints for project management, cost estimation, and AI chat
- Integrates AI services for intelligent recommendations and document processing
- Handles authentication, authorization, and observability
- Orchestrates complex business workflows and document ingestion

## 🏗️ Architecture Overview

```mermaid
graph TB
    Client[🌐 Web Frontend] --> Gateway[🚪 FastAPI Gateway]
    MCP[🤖 MCP Servers] --> Gateway
    
    Gateway --> Auth[🔐 Auth Router]
    Gateway --> Projects[📋 Projects Router]
    Gateway --> Chat[💬 Chat Router]
    Gateway --> Docs[📄 Documents Router]
    Gateway --> Estimation[💰 Estimation Router]
    
    Auth --> AuthService[🔐 Auth Service]
    Projects --> DB[(🗄️ PostgreSQL)]
    Chat --> LLMService[🧠 LLM Service]
    Docs --> IngestionService[📄 Ingestion Service]
    Estimation --> EstimationService[💰 Estimation Service]
    
    IngestionService --> MinIO[📦 MinIO Storage]
    IngestionService --> OCRService[👁️ OCR Service]
    LLMService --> Langfuse[📊 Langfuse]
```

## 📊 Core Data Models

### **Project Management Models**

```python
# Project - Central organizing unit for all work
class Project(Base):
    id: UUID                    # Unique project identifier  
    name: str                   # Project name
    client_name: str            # Client information
    status: str                 # draft, active, completed, archived
    start_date: Date            # Project start date
    due_date: Date              # Project deadline
    budget_planned: Decimal     # Planned budget (NIS)
    budget_actual: Decimal      # Actual costs (NIS)
    board_id: str               # Trello board integration ID

# Plan - Versioned project plans with cost estimates
class Plan(Base):
    id: str                     # ULID identifier
    project_id: str             # Foreign key to Project
    version: int                # Plan version number
    status: str                 # draft, approved, archived
    margin_target: Decimal      # Target profit margin
    currency: str               # Currency (default: NIS)

# PlanItem - Individual line items within plans  
class PlanItem(Base):
    id: str                     # ULID identifier
    plan_id: str                # Foreign key to Plan
    category: str               # materials, labor, equipment
    title: str                  # Item title/description
    quantity: Decimal           # Item quantity
    unit: str                   # Unit of measure
    unit_price: Decimal         # Price per unit (NIS)
    vendor_id: str              # Associated vendor
    labor_hours: Decimal        # Labor hours if applicable
    subtotal: Decimal           # Calculated subtotal
```

### **Resource Management Models**

```python
# Vendor - Supplier and contractor information
class Vendor(Base):
    id: UUID                    # Unique vendor identifier
    name: str                   # Vendor name
    contact: JSON               # Contact information
    rating: int                 # Vendor rating (1-5)

# Material - Product and material specifications
class Material(Base):
    id: UUID                    # Unique material identifier
    name: str                   # Material name
    spec: str                   # Technical specifications
    unit: str                   # Unit of measure
    category: str               # Material category

# VendorPrice - Pricing information from vendors
class VendorPrice(Base):
    id: str                     # ULID identifier
    vendor_id: str              # Foreign key to Vendor
    material_id: str            # Foreign key to Material
    price_nis: Decimal          # Price in NIS
    confidence: Decimal         # Confidence score (0.0-1.0)
    is_quote: bool              # Whether this is a formal quote
```

### **Document and AI Models**

```python
# Document - File storage and processing
class Document(Base):
    id: str                     # ULID identifier
    filename: str               # Original filename
    type: str                   # quote, invoice, project_brief, etc.
    project_id: str             # Associated project
    storage_path: str           # Path in MinIO storage
    content_sha256: str         # Content hash for deduplication

# ChatSession - AI conversation management
class ChatSession(Base):
    id: str                     # ULID identifier
    project_id: str             # Associated project
    title: str                  # Session title
    context: JSON               # Session context
    is_active: bool             # Whether session is active

# ExtractedItem - Items extracted from documents
class ExtractedItem(Base):
    id: str                     # ULID identifier
    document_id: str            # Source document
    type: str                   # line_item, purchase, shipping
    title: str                  # Item title
    qty: Decimal                # Quantity
    unit_price_nis: Decimal     # Unit price in NIS
    confidence: Decimal         # Extraction confidence
```

## 🔌 API Router Structure

### **Core Business Routers**

#### **Projects Router** (`/projects`)
- `GET /projects` - List all projects with filtering
- `POST /projects` - Create new project
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

**Key Features:**
- Project lifecycle management
- Integration with plans and documents
- Status tracking and analytics

#### **Plans Router** (`/plans`)
- `GET /plans` - List plans (filterable by project)
- `POST /plans` - Create new plan version
- `GET /plans/{id}/estimate` - Get comprehensive cost estimate
- `POST /plans/{id}/items` - Add items to plan
- `POST /plans/{id}/approve` - Approve plan version

**Key Features:**
- Versioned plan management
- Real-time cost calculation
- Item-level cost tracking

#### **Chat Router** (`/chat`)
- `POST /chat/message` - Send message to AI assistant
- `GET /chat/sessions` - List chat sessions
- `POST /chat/plan-suggestion` - Get AI plan suggestions
- `POST /chat/cost-estimate` - Get cost estimates via chat

**AI Integration:**
- Context-aware responses using project data
- RAG system for knowledge retrieval
- Memory management across sessions
- Multi-language support (Hebrew/English)

#### **Documents Router** (`/documents`)
- `POST /documents/upload` - Upload documents with processing
- `GET /documents/{id}/extracted` - Get extracted items
- `POST /documents/{id}/process` - Trigger document processing
- `GET /documents/{id}/chunks` - Get document text chunks

**Processing Pipeline:**
1. **Upload & Store**: Save to MinIO with metadata
2. **Classify**: Identify document type (quote, invoice, etc.)
3. **Extract**: OCR and text extraction
4. **Process**: AI-powered item extraction
5. **Validate**: Quality checks and confidence scoring

### **Resource Management Routers**

#### **Vendors Router** (`/vendors`)
- Standard CRUD operations
- `GET /vendors/{id}/prices` - Get vendor pricing history
- `POST /vendors/{id}/quote` - Request formal quote

#### **Materials Router** (`/materials`)
- Material catalog management
- `GET /materials/search` - Search by specifications
- `GET /materials/{id}/prices` - Current market pricing

#### **Estimation Router** (`/estimation`)
- `POST /estimation/shipping` - Calculate shipping costs
- `POST /estimation/labor` - Estimate labor requirements
- `POST /estimation/project` - Full project cost estimation
- `GET /estimation/accuracy` - Historical accuracy metrics

## 🛠️ Service Layer

### **Estimation Service**

**Key Capabilities:**
```python
class EstimationService:
    def estimate_shipping(self, request: ShippingEstimateRequest) -> ShippingEstimate:
        # Multi-method shipping (Standard, Express, Freight, Local)
        # Historical data integration for improved accuracy
        # Confidence scoring and surcharge calculations
        
    def estimate_labor(self, request: LaborEstimateRequest) -> LaborEstimate:
        # Role-based rates with efficiency factors
        # Project complexity adjustments
        # Lead time and scheduling considerations
        
    def estimate_project(self, request: ProjectEstimateRequest) -> ProjectEstimate:
        # Comprehensive cost breakdown
        # Material, labor, and shipping integration
        # Margin and risk analysis
```

### **Ingestion Service**

**Document Processing Pipeline:**
```python
class IngestionService:
    async def process_document(self, document_id: str) -> ProcessingResult:
        # 1. Classification: Identify document type
        # 2. OCR: Extract text content
        # 3. Chunking: Split for searchable segments
        # 4. AI Extraction: Extract line items, vendors, prices
        # 5. Validation: Quality checks and matching
        # 6. Integration: Link to projects and update pricing
```

**AI-Powered Extraction:**
- Vendor name matching and standardization
- Material specification recognition
- Price validation against market data
- Confidence scoring for all extracted data

### **LLM Service**

**AI Integration:**
```python
class LLMService:
    async def process_chat_message(self, message: str, context: dict) -> str:
        # Context injection with project data
        # RAG system integration for knowledge retrieval
        # Multi-language response generation
        # Memory management for conversation continuity
        
    async def extract_structured_data(self, text: str, schema: Schema) -> dict:
        # Document analysis and item extraction
        # Structured data extraction with validation
        # Confidence scoring and quality assessment
```

### **Auth Service**

**Security Features:**
- JWT-based authentication with refresh tokens
- bcrypt password hashing
- Role-based access control
- Session management and security monitoring

## 🔐 Security and Authentication

### **Authentication Flow**
1. **Login**: Username/password validation
2. **Token Generation**: JWT access and refresh tokens
3. **Request Authentication**: Token validation middleware
4. **Session Management**: Secure session handling

### **Security Measures**
- **Password Security**: bcrypt hashing with salt
- **CORS Protection**: Restricted origins for web app
- **Input Validation**: Pydantic schemas for all inputs
- **Rate Limiting**: API endpoint protection (planned)
- **Error Handling**: No sensitive data in error responses

## 📊 Database Integration

### **Connection Management**
```python
# PostgreSQL with connection pooling
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency injection for requests
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### **Query Optimization**
- **Efficient Joins**: Optimized relationship loading
- **Pagination**: Large result set handling
- **Indexing**: Performance-critical field indexing
- **Lazy Loading**: Load related data only when needed

## 🔄 Observability and Monitoring

### **Langfuse Integration**
```python
# Request tracing and AI operation monitoring
with observability_service.trace("project_creation") as trace:
    # Track business operations
    project = await create_project(data)
    
    # Monitor AI operations
    ai_response = await llm_service.generate_suggestions(project)
    trace.generation(
        model="claude-3",
        input=prompt,
        output=ai_response,
        usage={"input_tokens": 150, "output_tokens": 500}
    )
```

### **Monitoring Features**
- **Request Tracing**: Full request lifecycle tracking
- **AI Monitoring**: LLM call performance and cost tracking
- **Error Tracking**: Comprehensive error logging with context
- **Performance Metrics**: Response times and resource usage
- **Health Checks**: Service health and dependency monitoring

## 🧪 Testing Strategy

### **Test Coverage**
- **Unit Tests**: Individual service and router testing
- **Integration Tests**: Database and external service integration
- **E2E Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing

### **Example Test Patterns**
```python
# Router testing
async def test_create_project():
    response = client.post("/projects", json=project_data)
    assert response.status_code == 200
    assert response.json()["name"] == project_data["name"]

# Service testing  
async def test_estimation_service():
    estimate = estimation_service.estimate_shipping(request)
    assert estimate.total_cost > 0
    assert estimate.confidence > 0.5
```

## 🚀 Performance and Scalability

### **Performance Features**
- **Async Operations**: FastAPI async/await for I/O
- **Connection Pooling**: Efficient database connections
- **Response Streaming**: Large file streaming support
- **Caching**: Strategic caching for frequently accessed data

### **Scalability Considerations**
- **Stateless Design**: Horizontal scaling capability
- **Database Optimization**: Efficient queries and indexes
- **Background Tasks**: Async processing for heavy operations
- **Resource Management**: Memory and CPU optimization

## 🔧 Configuration and Environment

### **Key Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://studioops:studioops123@localhost:5432/studioops

# AI Services
OPENAI_API_KEY=your_openai_key
LANGFUSE_PUBLIC_KEY=your_langfuse_key
LANGFUSE_SECRET_KEY=your_langfuse_secret

# Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=studioops
MINIO_SECRET_KEY=studioops123

# Security
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

### **Startup and Health Checks**
```python
# Health check endpoint
@app.get("/health")
async def health_check():
    # Database connectivity check
    # External service health validation
    # System resource monitoring
    return {"status": "healthy", "database": "connected"}
```

The API Backend provides a robust, scalable foundation for StudioOps AI, handling all business logic, data management, and AI integrations while maintaining high performance and security standards.