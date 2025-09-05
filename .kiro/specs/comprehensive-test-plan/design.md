# Design Document

## Overview

This design establishes a comprehensive testing framework for the StudioOps AI system that addresses critical gaps in current testing coverage. Based on analysis of the existing codebase, the system has fragmented testing with several failing Playwright tests, incomplete unit test coverage, and unresolved Langfuse import issues. This design provides a systematic approach to create robust, maintainable tests across all system layers.

## Architecture Analysis

### Current System Architecture
The StudioOps AI system consists of:

**Frontend (Next.js/React):**
- Main application at `apps/web/src/app/page.tsx`
- Components: Chat, PlanEditor, ProjectForm, VendorForm, MaterialForm, Sidebar
- Hooks: useApi, useMaterials, useProjects, useVendors
- Context: ThemeContext

**Backend (FastAPI/Python):**
- Main API server at `apps/api/main.py`
- Routers: vendors, materials, chat, projects, plans, auth, estimation
- Services: observability_service, llm_service, estimation_service
- Middleware: ObservabilityMiddleware

**Database (PostgreSQL):**
- Connection via psycopg2
- Models for projects, vendors, materials, plans
- Vector support via pgvector

**Infrastructure:**
- Docker Compose setup with PostgreSQL, MinIO, Langfuse
- Environment-based configuration

### Current Testing Issues Identified

1. **Playwright Tests Failing:** All 5 Playwright tests are failing due to incorrect port configurations and missing navigation elements
2. **Langfuse Import Errors:** ModuleNotFoundError for langfuse.decorators (deprecated API)
3. **Incomplete Coverage:** Missing tests for critical components like database operations, configuration management
4. **Test Isolation:** No proper test data setup/cleanup mechanisms
5. **Performance Testing:** No load or performance testing framework

## Testing Strategy Design

### 1. Test Pyramid Architecture

```
    /\
   /  \     E2E Tests (Playwright)
  /____\    Integration Tests (API + DB)
 /      \   Unit Tests (Components + Services)
/________\  
```

**Unit Tests (70%):** Fast, isolated tests for individual components and functions
**Integration Tests (20%):** Tests for API endpoints, database operations, service interactions
**E2E Tests (10%):** Full user workflow tests using Playwright

### 2. Test Environment Strategy

**Test Isolation Levels:**
- **Unit Tests:** Mock all external dependencies
- **Integration Tests:** Use test database with transaction rollback
- **E2E Tests:** Use dedicated test environment with clean data

**Environment Configuration:**
- `test.env` for test-specific environment variables
- Test database with separate schema
- Mock services for external dependencies (Langfuse, OpenAI)

## Components and Interfaces

### 1. Frontend Testing Framework

**Technology Stack:**
- **Jest + React Testing Library:** Unit tests for React components
- **MSW (Mock Service Worker):** API mocking for frontend tests
- **Playwright:** E2E testing with real browser automation

**Component Test Structure:**
```typescript
// Component test template
describe('ComponentName', () => {
  beforeEach(() => {
    // Setup test data and mocks
  });
  
  it('renders correctly with props', () => {
    // Render and assertion tests
  });
  
  it('handles user interactions', () => {
    // Event simulation and state verification
  });
  
  it('handles error states', () => {
    // Error boundary and error state tests
  });
});
```

### 2. Backend Testing Framework

**Technology Stack:**
- **pytest:** Python testing framework
- **FastAPI TestClient:** API endpoint testing
- **pytest-asyncio:** Async test support
- **factory_boy:** Test data generation
- **pytest-postgresql:** Test database management

**API Test Structure:**
```python
# API test template
class TestAPIEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_endpoint_success(self, client):
        # Test successful API calls
        
    def test_endpoint_validation(self, client):
        # Test input validation
        
    def test_endpoint_error_handling(self, client):
        # Test error scenarios
```

### 3. Database Testing Framework

**Test Database Strategy:**
- Separate test database: `studioops_test`
- Transaction-based test isolation
- Automated schema migration for tests
- Test data factories for consistent data generation

**Database Test Structure:**
```python
class TestDatabaseOperations:
    @pytest.fixture
    def db_session(self):
        # Create test database session with rollback
        
    def test_crud_operations(self, db_session):
        # Test Create, Read, Update, Delete
        
    def test_data_integrity(self, db_session):
        # Test constraints and relationships
```

### 4. Observability Testing Framework

**Langfuse Integration Testing:**
- Mock Langfuse client for unit tests
- Test observability service initialization
- Validate trace creation and error handling
- Test middleware integration

**Observability Test Structure:**
```python
class TestObservabilityService:
    @pytest.fixture
    def mock_langfuse(self):
        # Mock Langfuse client
        
    def test_trace_creation(self, mock_langfuse):
        # Test trace and span creation
        
    def test_error_tracking(self, mock_langfuse):
        # Test error capture and reporting
```

## Data Models

### Test Data Management

**Test Data Factories:**
```python
# Factory definitions for consistent test data
class ProjectFactory(factory.Factory):
    class Meta:
        model = Project
    
    name = factory.Faker('company')
    description = factory.Faker('text')
    created_at = factory.LazyFunction(datetime.now)

class VendorFactory(factory.Factory):
    class Meta:
        model = Vendor
    
    name = factory.Faker('company')
    contact = factory.Faker('phone_number')
    rating = factory.Faker('pyfloat', min_value=1.0, max_value=5.0)
```

**Test Database Schema:**
- Mirror production schema in test environment
- Additional test-specific tables for test metadata
- Automated cleanup procedures

### Test Configuration Model

```python
@dataclass
class TestConfig:
    database_url: str
    api_base_url: str
    frontend_url: str
    langfuse_mock: bool
    test_data_path: str
    cleanup_after_tests: bool
```

## Error Handling

### Test Error Categories

1. **Setup Errors:** Database connection, environment configuration
2. **Execution Errors:** Test failures, assertion errors
3. **Cleanup Errors:** Data cleanup, resource deallocation
4. **Infrastructure Errors:** Docker services, network issues

### Error Handling Strategy

**Graceful Degradation:**
- Continue tests when non-critical services fail
- Provide clear error messages for debugging
- Automatic retry for flaky tests

**Error Reporting:**
- Structured error logs with context
- Screenshot capture for E2E test failures
- Performance metrics for failed tests

## Testing Strategy

### 1. Unit Testing Strategy

**Frontend Unit Tests:**
- **Component Rendering:** Test all components render correctly with various props
- **User Interactions:** Test button clicks, form submissions, navigation
- **State Management:** Test React hooks, context providers, state updates
- **Error Boundaries:** Test error handling and fallback UI

**Backend Unit Tests:**
- **Service Functions:** Test business logic in isolation
- **Data Validation:** Test Pydantic models and validation rules
- **Utility Functions:** Test helper functions and data transformations
- **Configuration Loading:** Test environment variable handling

### 2. Integration Testing Strategy

**API Integration Tests:**
- **Endpoint Testing:** Test all API routes with various inputs
- **Authentication:** Test protected routes and JWT handling
- **Database Integration:** Test API endpoints with real database operations
- **External Service Integration:** Test with mocked external services

**Database Integration Tests:**
- **CRUD Operations:** Test all database operations
- **Transaction Handling:** Test rollback and commit scenarios
- **Constraint Validation:** Test foreign keys and unique constraints
- **Performance:** Test query performance and connection pooling

### 3. End-to-End Testing Strategy

**User Workflow Tests:**
- **Project Management:** Complete project creation, editing, deletion flow
- **Chat Functionality:** Message sending, AI responses, plan generation
- **Navigation:** Test all page navigation and routing
- **Data Persistence:** Test data survives page refreshes and navigation

**Cross-Browser Testing:**
- Test on Chrome, Firefox, Safari
- Test responsive design on different screen sizes
- Test accessibility features

### 4. Performance Testing Strategy

**Load Testing:**
- API endpoint performance under load
- Database query performance
- Concurrent user simulation

**Frontend Performance:**
- Page load times
- Component render performance
- Bundle size optimization

## Implementation Phases

### Phase 1: Foundation Setup
1. Configure test environments and databases
2. Set up test frameworks (Jest, pytest, Playwright)
3. Create test data factories and utilities
4. Implement basic test infrastructure

### Phase 2: Unit Test Implementation
1. Frontend component tests
2. Backend service tests
3. Database operation tests
4. Configuration and utility tests

### Phase 3: Integration Test Implementation
1. API endpoint tests
2. Database integration tests
3. Service integration tests
4. Observability integration tests

### Phase 4: E2E Test Implementation
1. User workflow tests
2. Cross-browser compatibility tests
3. Performance and load tests
4. Accessibility tests

### Phase 5: CI/CD Integration
1. Automated test execution
2. Test reporting and metrics
3. Performance monitoring
4. Test maintenance procedures

## Success Criteria

1. **Test Coverage:** Achieve >90% code coverage for critical components
2. **Test Reliability:** <5% flaky test rate
3. **Performance:** All tests complete within 10 minutes
4. **Maintainability:** Clear test structure and documentation
5. **Integration:** Seamless CI/CD integration with automated reporting

This comprehensive testing design ensures robust validation of all system components while providing maintainable, reliable test infrastructure for ongoing development.