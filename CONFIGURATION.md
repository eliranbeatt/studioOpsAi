# StudioOps AI Configuration Guide

## Environment Setup

StudioOps AI uses environment variables for configuration. Choose the appropriate template:

### Development Environment
```bash
python config_manager.py setup --env development
```

### Production Environment  
```bash
python config_manager.py setup --env production
```

### Custom Configuration
```bash
python config_manager.py setup --env template
# Then edit .env with your specific values
```

## Configuration Validation

Validate your configuration:
```bash
python config_manager.py validate
```

Check external service connectivity:
```bash
python config_manager.py check-services
```

## Required Configuration

### Database (Required)
- `DATABASE_URL`: PostgreSQL connection URL
- `DB_POOL_SIZE`: Connection pool size (default: 10)

### API Server (Required)
- `API_HOST`: Server host (default: 127.0.0.1)
- `API_PORT`: Server port (default: 8003)

## Optional Configuration

### External Services
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `TRELLO_API_KEY`: Trello API key for project boards
- `TRELLO_API_TOKEN`: Trello API token
- `MINIO_ENDPOINT`: MinIO endpoint for file storage

### Security
- `JWT_SECRET_KEY`: JWT signing secret (use strong random key)
- `API_CORS_ENABLED`: Enable CORS (default: true for development)

### Logging
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FORMAT`: Log format (human, json)

## Production Security

For production deployments:
1. Use strong random values for secrets
2. Set `DEVELOPMENT_MODE=false`
3. Set `DEBUG_ENABLED=false`
4. Use environment variables or secrets management for sensitive values
5. Enable appropriate security headers and rate limiting

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify database server is running
   - Check network connectivity

2. **MinIO Connection Failed**
   - Verify MINIO_ENDPOINT is accessible
   - Check MINIO_ACCESS_KEY and MINIO_SECRET_KEY
   - Verify MINIO_SECURE setting matches your setup

3. **External API Errors**
   - Verify API keys are valid and active
   - Check network connectivity
   - Review API rate limits

### Getting Help

Run configuration validation for detailed error messages:
```bash
python config_manager.py validate
```

Check service connectivity:
```bash
python config_manager.py check-services
```
