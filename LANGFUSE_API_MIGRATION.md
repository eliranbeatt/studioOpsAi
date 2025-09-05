# Langfuse API Migration Guide

## Overview

This document outlines the migration from deprecated Langfuse v2.x APIs to the supported v3.3.4+ APIs. The main change involves replacing the deprecated `langfuse.context` API with the new `langfuse.get_current_trace()` method.

## Changes Made

### 1. Deprecated API Usage (v2.x)
```python
# OLD - DEPRECATED
trace_id = getattr(observability_service.langfuse.context, 'get_current_trace_id', lambda: None)()
```

### 2. New API Usage (v3.3.4+)
```python
# NEW - SUPPORTED
trace_id = observability_service.get_current_trace_id()
```

## Updated Observability Service

The `ObservabilityService` class now provides a proper abstraction for the new Langfuse API:

### New Method: `get_current_trace_id()`
```python
def get_current_trace_id(self) -> Optional[str]:
    """
    Get the current trace ID using the new Langfuse API (v3.3.4+)
    
    Note: This replaces the deprecated langfuse.context API from v2.x
    
    Returns:
        Optional[str]: Current trace ID if available, None if disabled or error
    """
    if not self.enabled:
        return None
        
    try:
        # Use the new Langfuse API to get current trace
        current_trace = self.langfuse.get_current_trace()
        if current_trace:
            return current_trace.id
        return None
    except Exception as e:
        logger.error(f"Failed to get current trace ID: {e}")
        return None
```

## Files Updated

1. **`apps/api/services/observability_service.py`**
   - Added `get_current_trace_id()` method using new Langfuse API
   - Updated documentation to indicate v3.3.4+ compatibility

2. **`apps/api/services/estimation_service.py`**
   - Replaced deprecated context access with new method call
   - Lines 138, 155, 179 updated to use `observability_service.get_current_trace_id()`

## Prevention Measures

### 1. Code Scanning
Regularly scan for deprecated Langfuse API usage:
```bash
# Search for deprecated context usage
grep -r "langfuse\.context" apps/

# Search for direct context method calls
grep -r "get_current_trace_id" apps/ | grep -v "def get_current_trace_id"
```

### 2. Import Validation
Ensure only the new API patterns are used:
```python
# ✅ CORRECT - Use the service abstraction
from ..services.observability_service import observability_service
trace_id = observability_service.get_current_trace_id()

# ❌ INCORRECT - Direct deprecated access
trace_id = getattr(observability_service.langfuse.context, 'get_current_trace_id', lambda: None)()
```

### 3. Testing
Include API compatibility tests in the test suite:
```python
def test_langfuse_api_compatibility():
    """Test that we're using supported Langfuse APIs"""
    # Should not use deprecated context API
    assert not hasattr(observability_service.langfuse, 'context'), \
        "Deprecated langfuse.context API should not be used"
    
    # Should use the new service method
    assert hasattr(observability_service, 'get_current_trace_id'), \
        "New get_current_trace_id method should be available"
```

## Version Compatibility

- **Langfuse v2.x**: Uses deprecated `langfuse.context` API
- **Langfuse v3.3.4+**: Uses new `langfuse.get_current_trace()` API
- **This codebase**: Compatible with Langfuse v3.3.4+

## Error Handling

The new implementation includes proper error handling:
- Gracefully handles disabled observability
- Logs errors but doesn't crash the application
- Returns None instead of raising exceptions

## Backward Compatibility

The changes maintain backward compatibility:
- Same method signature and return type
- Same behavior when observability is disabled
- No breaking changes to existing code

## Future Maintenance

1. **Monitor Langfuse Releases**: Watch for API changes in future versions
2. **Regular Code Scans**: Periodically check for deprecated API usage
3. **Update Documentation**: Keep this guide current with API changes
4. **Test Coverage**: Ensure tests cover all observability service methods

## Related Files

- `apps/api/services/observability_service.py` - Main observability service
- `apps/api/services/estimation_service.py` - Example usage of new API
- `test_observability.py` - Test script for observability functionality
- `apps/api/middleware/observability_middleware.py` - Middleware using observability service

## Troubleshooting

If you encounter import errors related to Langfuse:

1. **Clear Python cache**:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

2. **Check Langfuse version**:
   ```bash
   pip show langfuse
   ```

3. **Verify environment variables**:
   ```bash
   echo $LANGFUSE_PUBLIC_KEY $LANGFUSE_SECRET_KEY $LANGFUSE_HOST
   ```

4. **Run observability tests**:
   ```bash
   python test_observability.py
   ```