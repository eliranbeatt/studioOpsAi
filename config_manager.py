#!/usr/bin/env python3
"""
Configuration Management Utility
Provides tools for managing StudioOps AI configuration
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, List

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # dotenv not available, skip loading
    pass

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from apps.api.services.config_validation_service import config_validator, ConfigSeverity

def setup_environment(env_type: str = "development"):
    """Set up environment configuration from template"""
    
    templates = {
        'development': '.env.development',
        'production': '.env.production',
        'template': '.env.template'
    }
    
    if env_type not in templates:
        print(f"❌ Unknown environment type: {env_type}")
        print(f"Available types: {', '.join(templates.keys())}")
        return False
    
    template_file = project_root / templates[env_type]
    target_file = project_root / '.env'
    
    if not template_file.exists():
        print(f"❌ Template file not found: {template_file}")
        return False
    
    # Check if .env already exists
    if target_file.exists():
        response = input(f"⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return False
    
    try:
        shutil.copy2(template_file, target_file)
        print(f"✅ Environment configuration set up from {templates[env_type]}")
        print(f"📝 Please edit {target_file} with your actual configuration values")
        
        if env_type == 'production':
            print("🔒 Remember to set sensitive values via environment variables or secrets management")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up environment: {e}")
        return False

def validate_configuration():
    """Validate current configuration"""
    print("🔍 Validating StudioOps AI configuration...")
    
    # Run validation
    results = config_validator.validate_all()
    summary = config_validator.get_validation_summary()
    
    # Print summary
    config_validator.print_validation_report()
    
    return summary['is_valid']

def check_required_services():
    """Check if required external services are accessible"""
    print("\n🔍 Checking external service accessibility...")
    
    services_to_check = [
        ('Database', check_database),
        ('MinIO', check_minio),
        ('Trello API', check_trello),
        ('OpenAI API', check_openai)
    ]
    
    results = {}
    for service_name, check_func in services_to_check:
        try:
            result = check_func()
            results[service_name] = result
            status = "✅" if result['accessible'] else "❌"
            print(f"{status} {service_name}: {result['message']}")
        except Exception as e:
            results[service_name] = {'accessible': False, 'message': f"Error: {e}"}
            print(f"❌ {service_name}: Error - {e}")
    
    return results

def check_database():
    """Check database connectivity"""
    import psycopg2
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        return {'accessible': False, 'message': 'DATABASE_URL not configured'}
    
    try:
        conn = psycopg2.connect(db_url, connect_timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {'accessible': True, 'message': 'Database connection successful'}
    except Exception as e:
        return {'accessible': False, 'message': f'Connection failed: {e}'}

def check_minio():
    """Check MinIO connectivity"""
    try:
        from minio import Minio
        
        endpoint = os.getenv('MINIO_ENDPOINT')
        access_key = os.getenv('MINIO_ACCESS_KEY')
        secret_key = os.getenv('MINIO_SECRET_KEY')
        
        if not all([endpoint, access_key, secret_key]):
            return {'accessible': False, 'message': 'MinIO credentials not configured'}
        
        client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        )
        
        buckets = list(client.list_buckets())
        return {'accessible': True, 'message': f'MinIO accessible, {len(buckets)} buckets found'}
        
    except ImportError:
        return {'accessible': False, 'message': 'MinIO client not installed (pip install minio)'}
    except Exception as e:
        return {'accessible': False, 'message': f'Connection failed: {e}'}

def check_trello():
    """Check Trello API connectivity"""
    import requests
    
    api_key = os.getenv('TRELLO_API_KEY')
    api_token = os.getenv('TRELLO_API_TOKEN') or os.getenv('TRELLO_TOKEN')
    
    if not all([api_key, api_token]):
        return {'accessible': False, 'message': 'Trello API credentials not configured'}
    
    try:
        response = requests.get(
            "https://api.trello.com/1/members/me",
            params={"key": api_key, "token": api_token},
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return {'accessible': True, 'message': f'Trello API accessible for user: {user_data.get("username", "unknown")}'}
        else:
            return {'accessible': False, 'message': f'Trello API error: {response.status_code}'}
            
    except Exception as e:
        return {'accessible': False, 'message': f'Request failed: {e}'}

def check_openai():
    """Check OpenAI API connectivity"""
    import requests
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {'accessible': False, 'message': 'OpenAI API key not configured'}
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json()
            return {'accessible': True, 'message': f'OpenAI API accessible, {len(models.get("data", []))} models available'}
        else:
            return {'accessible': False, 'message': f'OpenAI API error: {response.status_code}'}
            
    except Exception as e:
        return {'accessible': False, 'message': f'Request failed: {e}'}

def generate_config_docs():
    """Generate configuration documentation"""
    print("📝 Generating configuration documentation...")
    
    docs_content = """# StudioOps AI Configuration Guide

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
"""
    
    docs_file = project_root / 'CONFIGURATION.md'
    try:
        with open(docs_file, 'w') as f:
            f.write(docs_content)
        print(f"✅ Configuration documentation generated: {docs_file}")
        return True
    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        return False

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='StudioOps AI Configuration Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up environment configuration')
    setup_parser.add_argument('--env', choices=['development', 'production', 'template'], 
                             default='development', help='Environment type')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    
    # Check services command
    check_parser = subparsers.add_parser('check-services', help='Check external service connectivity')
    
    # Generate docs command
    docs_parser = subparsers.add_parser('generate-docs', help='Generate configuration documentation')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        success = setup_environment(args.env)
        sys.exit(0 if success else 1)
    
    elif args.command == 'validate':
        is_valid = validate_configuration()
        sys.exit(0 if is_valid else 1)
    
    elif args.command == 'check-services':
        results = check_required_services()
        accessible_count = sum(1 for r in results.values() if r['accessible'])
        total_count = len(results)
        print(f"\n📊 Services: {accessible_count}/{total_count} accessible")
        sys.exit(0 if accessible_count == total_count else 1)
    
    elif args.command == 'generate-docs':
        success = generate_config_docs()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()