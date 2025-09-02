# Observability with Langfuse

This document describes the observability setup for StudioOps AI using Langfuse for tracing, monitoring, and debugging.

## Overview

The StudioOps AI API includes comprehensive observability features powered by Langfuse. This enables:

- **Request Tracing**: Automatic tracing of all HTTP requests
- **Performance Monitoring**: Tracking of response times and latency
- **Error Tracking**: Detailed error logging with context
- **LLM Observability**: Monitoring of AI model calls and responses
- **Custom Events**: Application-specific event tracking

## Setup

### 1. Environment Variables

Add the following to your `.env` file:

```bash
# Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=http://localhost:3000
```

### 2. Docker Compose

The Langfuse service is already configured in `infra/docker-compose.yaml`. It will automatically start with:

```bash
cd infra
docker-compose up -d
```

### 3. Getting Langfuse Keys

1. Visit http://localhost:3000 (Langfuse UI)
2. Create an account
3. Go to Settings → API Keys
4. Create a new public/secret key pair
5. Update your `.env` file with the new keys

## Features

### Automatic Request Tracing

All HTTP requests are automatically traced with:
- Request method and path
- Query parameters
- Headers (excluding sensitive ones)
- Response status codes
- Processing time
- User context (when authenticated)

### Custom Event Tracking

The observability service provides methods for tracking:

```python
from services.observability_service import observability_service

# Create traces
trace_id = observability_service.create_trace(name="operation_name")

# Track spans within traces
span_id = observability_service.create_span(trace_id, "span_name")

# Track custom events
event_id = observability_service.create_event(trace_id, "event_name")

# Track errors with context
error_id = observability_service.track_error(
    trace_id, 
    "ErrorType", 
    "Error message", 
    context={"additional": "data"}
)
```

### Integration with Services

#### Estimation Service

The estimation service automatically tracks:
- Shipping cost estimations
- Labor cost estimations  
- Project cost estimations
- Historical data lookups
- Error cases and fallbacks

#### Authentication

User authentication events are tracked with:
- Login attempts
- Token generation
- API key usage
- Permission checks

## API Endpoints

### Health Check

```http
GET /api/observability/health
```

Response:
```json
{
  "status": "enabled",
  "service": "langfuse",
  "details": {
    "initialized": true,
    "public_key_configured": true,
    "secret_key_configured": true,
    "host": "http://localhost:3000"
  }
}
```

## Usage Examples

### Manual Tracing

```python
from services.observability_service import observability_service

# Start a trace
trace_id = observability_service.create_trace(
    name="custom_operation",
    user_id="user_123",
    metadata={"custom": "data"}
)

# Track operations within the trace
span_id = observability_service.create_span(
    trace_id=trace_id,
    name="database_query",
    metadata={"query": "SELECT * FROM table"}
)

# Track completion
observability_service.create_span(
    trace_id=trace_id,
    name="operation_complete",
    metadata={"result": "success", "rows": 42}
)

# Flush events
observability_service.flush()
```

### Error Tracking

```python
try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    observability_service.track_error(
        trace_id=get_current_trace_id(),
        error_type=type(e).__name__,
        error_message=str(e),
        stack_trace=traceback.format_exc(),
        context={"operation": "risky_operation", "input": input_data}
    )
    raise
```

## Testing

Run the observability test script:

```bash
cd apps/api
python test_observability.py
```

This will test:
- Langfuse client initialization
- Trace creation
- Span creation  
- Event creation
- Error tracking
- Event flushing

## Monitoring

Access the Langfuse dashboard at http://localhost:3000 to:

- View request traces and timelines
- Analyze performance metrics
- Debug errors and exceptions
- Monitor LLM usage and costs
- Set up alerts and notifications

## Best Practices

1. **Include Context**: Always provide meaningful metadata with events
2. **Handle Errors Gracefully**: Use error tracking for all exception cases
3. **Flush Regularly**: Call `flush()` after important operations
4. **Use Meaningful Names**: Descriptive trace and span names help debugging
5. **Respect Privacy**: Avoid logging sensitive data in metadata

## Troubleshooting

### Langfuse Not Initializing

Check:
1. Environment variables are set correctly
2. Langfuse service is running (`docker-compose ps`)
3. Network connectivity to Langfuse host

### Events Not Appearing

1. Check if `observability_service.enabled` is True
2. Verify API keys have correct permissions
3. Check Langfuse dashboard for any API errors

### Performance Issues

1. Use async operations for non-blocking tracking
2. Batch events where possible
3. Consider rate limiting for high-volume applications