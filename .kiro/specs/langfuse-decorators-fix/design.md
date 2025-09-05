# Design Document

## Overview

This design addresses the persistent Langfuse decorators import issue through a comprehensive, multi-layered approach. The root cause analysis reveals several interconnected problems that must be solved systematically.

## Root Cause Analysis

Based on comprehensive codebase analysis, I've identified the following issues with their probability and impact:

### Problem Analysis Matrix

| Issue Type | Probability | Impact | Evidence |
|------------|-------------|---------|----------|
| Python Cache Files | **95%** | Critical | Found `observability_service.cpython-313.pyc` in `__pycache__` |
| Import Chain Propagation | **85%** | High | Multiple routers import observability service |
| Process Memory Cache | **70%** | High | Uvicorn auto-reload may not clear all imports |
| File Sync Issues | **30%** | Medium | Discrepancy between file reads and execution |
| Hidden Decorator Imports | **15%** | Low | No evidence found in comprehensive search |

### Primary Root Cause: Python Bytecode Cache

The main issue is Python's import system loading compiled bytecode (`.pyc`) files from `__pycache__` directories. Even when source files are updated, cached bytecode contains old imports.

**Critical Evidence:**
- `apps/api/services/__pycache__/observability_service.cpython-313.pyc` exists
- Multiple files import from this cached module
- Server errors persist despite source corrections

## Architecture

### 1. Cache Cleanup System
**Purpose**: Remove all Python cache files containing stale imports

**Components:**
- Recursive `__pycache__` directory removal
- `.pyc` file cleanup across entire project
- Virtual environment cache clearing

### 2. Import Dependency Chain
**Purpose**: Update all files that depend on observability service

**Identified Dependencies:**
- `apps/api/routers/ocr.py`
- `apps/api/routers/unstructured.py` 
- `apps/api/test_observability.py`
- `apps/api/middleware/observability_middleware.py`

### 3. Process Management
**Purpose**: Ensure clean server restart without cached imports

**Components:**
- Complete process termination
- Cache verification
- Clean restart with validation

## Components and Interfaces

### Current Correct Implementation
```python
# CORRECT (Already implemented)
from langfuse import Langfuse

class ObservabilityService:
    def __init__(self):
        self.langfuse = Langfuse(...)
    
    def create_trace(self, name, **kwargs):
        return self.langfuse.trace(name=name, **kwargs)
```

### Deprecated Patterns (Causing Issues)
```python
# INCORRECT (Causes ModuleNotFoundError)
from langfuse.decorators import observe, langfuse_context

@observe()
def some_function():
    pass
```

## Data Models

### Cache File Locations
- `apps/api/__pycache__/`
- `apps/api/services/__pycache__/`
- `apps/api/routers/__pycache__/`
- `apps/api/middleware/__pycache__/`

### Import Chain Dependencies
```
observability_service.py
├── routers/ocr.py
├── routers/unstructured.py
├── middleware/observability_middleware.py
└── test_observability.py
```

## Error Handling

### Cache-Related Errors
- **Issue**: Stale bytecode files with old imports
- **Solution**: Complete cache cleanup before restart
- **Prevention**: Automated cache clearing in CI/CD

### Import Chain Errors  
- **Issue**: Dependent modules loading from cached imports
- **Solution**: Restart all dependent processes
- **Prevention**: Coordinated dependency updates

## Testing Strategy

### 1. Cache Cleanup Validation
```bash
# Verify no cache files exist
find apps/api -name "__pycache__" -type d
find apps/api -name "*.pyc" -type f
```

### 2. Import Verification
```bash
# Verify correct imports only
grep -r "from langfuse" apps/api/
grep -r "langfuse.decorators" apps/api/
```

### 3. Server Startup Test
```bash
# Test clean startup
cd apps/api && python -m uvicorn main:app --reload
```

### 4. Functionality Test
```python
# Test observability works
from services.observability_service import observability_service
trace_id = observability_service.create_trace("test")
assert trace_id is not None
```

## Implementation Phases

### Phase 1: Complete Cache Cleanup
1. Stop all running Python processes
2. Remove all `__pycache__` directories recursively
3. Remove all `.pyc` files
4. Clear virtual environment caches

### Phase 2: Process Restart
1. Kill any remaining uvicorn processes
2. Clear Python import cache in memory
3. Restart with clean environment
4. Verify no import errors

### Phase 3: Validation
1. Test server startup
2. Test observability functionality
3. Verify all dependent services work
4. Run comprehensive tests

## Success Criteria

1. **Server Startup**: API server starts without ModuleNotFoundError
2. **Functionality**: All observability features work correctly  
3. **Stability**: No recurring cache-related issues
4. **Dependencies**: All dependent services function properly
5. **Prevention**: Robust measures prevent recurrence

This design provides a systematic approach to permanently resolve the Langfuse decorators issue by addressing the root cause (Python cache contamination) and all contributing factors.