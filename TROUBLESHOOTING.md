# StudioOps AI Troubleshooting Guide

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Service-Specific Issues](#service-specific-issues)
4. [Database Issues](#database-issues)
5. [Configuration Issues](#configuration-issues)
6. [Performance Issues](#performance-issues)
7. [Recovery Procedures](#recovery-procedures)
8. [Monitoring and Logs](#monitoring-and-logs)

## Quick Diagnostics

### System Health Check

Run the comprehensive system validation:

```bash
# Check configuration
python config_manager.py validate

# Check service connectivity
python config_manager.py check-services

# Test startup validation
python test_startup_validation.py
```

### Service Status Check

```bash
# Check API server status
curl http://localhost:8003/health

# Check database connectivity
python -c "
import psycopg2
import os
conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops'))
print('Database: Connected')
conn.close()
"

# Check MinIO connectivity
python -c "
from minio import Minio
import os
client = Minio(os.getenv('MINIO_ENDPOINT', 'localhost:9000'), 
               access_key=os.getenv('MINIO_ACCESS_KEY', 'studioops'),
               secret_key=os.getenv('MINIO_SECRET_KEY', 'studioops123'),
               secure=False)
print(f'MinIO: Connected, buckets: {[b.name for b in client.list_buckets()]}')
"
```

## Common Issues

### 1. Application Won't Start

**Symptoms:**
- API server fails to start
- Import errors or module not found
- Configuration validation errors

**Diagnosis:**
```bash
# Check configuration
python config_manager.py validate

# Check Python environment
python --version
pip list | grep -E "(fastapi|psycopg2|minio)"

# Check startup validation
python test_startup_validation.py
```

**Solutions:**

#### Missing Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Install specific missing packages
pip install fastapi psycopg2-binary minio requests python-dotenv
```

#### Configuration Issues
```bash
# Set up development environment
python config_manager.py setup --env development

# Edit .env file with correct values
notepad .env  # or your preferred editor
```

#### Database Connection
```bash
# Check if PostgreSQL is running
# On Windows:
Get-Service postgresql*

# Test database connection
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://studioops:studioops123@localhost:5432/studioops')
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

### 2. API Server Errors

**Symptoms:**
- HTTP 500 errors
- JSON serialization errors
- Timeout errors

**Diagnosis:**
```bash
# Check API server logs
tail -f logs/dev-studioops.log

# Test API endpoints
curl -X GET http://localhost:8003/health
curl -X GET http://localhost:8003/api/projects
```

**Solutions:**

#### JSON Serialization Errors
- Issue: Usually related to datetime objects in responses
- Fix: Ensure all datetime fields use ISO string format
- Check: `apps/api/utils/error_handling.py` for proper timestamp handling

#### Database Query Errors
```bash
# Check database schema
python -c "
import psycopg2
import os
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\';')
tables = cursor.fetchall()
print('Available tables:', [t[0] for t in tables])
cursor.close()
conn.close()
"
```

#### Port Conflicts
```bash
# Check which process is using port 8003
netstat -ano | findstr :8003

# Kill conflicting process (replace PID)
taskkill /F /PID <PID>

# Or use a different port
$env:API_PORT = "8004"
```

### 3. Frontend Issues

**Symptoms:**
- API calls failing
- Loading states not working
- Error messages not displaying

**Diagnosis:**
```bash
# Check frontend build
cd apps/web
npm run build

# Check API connectivity from frontend
curl -X GET http://localhost:8003/api/health

# Check browser console for errors
# Open Developer Tools > Console
```

**Solutions:**

#### API Connection Issues
- Check `NEXT_PUBLIC_API_URL` in environment
- Verify CORS settings in API server
- Check network connectivity

#### Build Issues
```bash
cd apps/web
npm install
npm run dev
```

## Service-Specific Issues

### MinIO Storage Issues

**Symptoms:**
- File upload failures
- Bucket access errors
- Connection timeouts

**Diagnosis:**
```bash
# Test MinIO connectivity
python config_manager.py check-services | grep MinIO

# Check MinIO server status
# If running locally:
curl http://localhost:9000/minio/health/live
```

**Solutions:**

#### MinIO Not Running
```bash
# Start MinIO server (example)
minio server C:\minio-data --console-address ":9001"

# Or using Docker
docker run -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=studioops" \
  -e "MINIO_ROOT_PASSWORD=studioops123" \
  minio/minio server /data --console-address ":9001"
```

#### Bucket Creation Issues
```python
# Create required buckets
from minio import Minio
import os

client = Minio(
    os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY', 'studioops'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'studioops123'),
    secure=False
)

buckets = ['dev-documents', 'dev-uploads', 'dev-exports', 'dev-temp']
for bucket in buckets:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f'Created bucket: {bucket}')
```

### Trello Integration Issues

**Symptoms:**
- Board creation failures
- API authentication errors
- Card operations failing

**Diagnosis:**
```bash
# Test Trello API connectivity
python config_manager.py check-services | grep Trello

# Test Trello API directly
curl "https://api.trello.com/1/members/me?key=YOUR_API_KEY&token=YOUR_TOKEN"
```

**Solutions:**

#### API Credentials
1. Get API key from: https://trello.com/app-key
2. Generate token: https://trello.com/1/authorize?expiration=never&scope=read,write,account&response_type=token&name=StudioOps&key=YOUR_API_KEY
3. Update `.env` file:
   ```
   TRELLO_API_KEY=your_actual_api_key
   TRELLO_API_TOKEN=your_actual_token
   ```

#### Board Access Issues
```python
# Test board access
import requests
import os

api_key = os.getenv('TRELLO_API_KEY')
token = os.getenv('TRELLO_API_TOKEN')

response = requests.get(
    f"https://api.trello.com/1/members/me/boards",
    params={"key": api_key, "token": token}
)
print(f"Boards: {response.json()}")
```

### OpenAI Integration Issues

**Symptoms:**
- AI response failures
- Authentication errors
- Rate limit errors

**Diagnosis:**
```bash
# Test OpenAI API connectivity
python config_manager.py check-services | grep OpenAI

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Solutions:**

#### API Key Issues
1. Get API key from: https://platform.openai.com/api-keys
2. Update `.env` file:
   ```
   OPENAI_API_KEY=sk-your_actual_api_key
   ```

#### Rate Limiting
- Implement exponential backoff (already in ai_service.py)
- Consider upgrading API plan
- Monitor usage at: https://platform.openai.com/usage

## Database Issues

### Connection Issues

**Symptoms:**
- Database connection refused
- Timeout errors
- Authentication failures

**Diagnosis:**
```bash
# Check PostgreSQL service
Get-Service postgresql*

# Test connection
psql -h localhost -p 5432 -U studioops -d studioops

# Check connection string
echo $DATABASE_URL
```

**Solutions:**

#### PostgreSQL Not Running
```bash
# Start PostgreSQL service
Start-Service postgresql-x64-14  # Adjust version as needed

# Or restart
Restart-Service postgresql-x64-14
```

#### Database Doesn't Exist
```sql
-- Connect as superuser
psql -h localhost -p 5432 -U postgres

-- Create database and user
CREATE DATABASE studioops;
CREATE USER studioops WITH PASSWORD 'studioops123';
GRANT ALL PRIVILEGES ON DATABASE studioops TO studioops;
```

### Schema Issues

**Symptoms:**
- Missing table errors
- Foreign key constraint errors
- Migration failures

**Diagnosis:**
```bash
# Check database schema
python test_startup_validation.py | grep -A 10 "Database schema"

# Run schema validation
python -c "
import psycopg2
import os
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\';')
print('Tables:', [t[0] for t in cursor.fetchall()])
cursor.close()
conn.close()
"
```

**Solutions:**

#### Run Database Migration
```bash
# Run the migration script
python database_migration_script.py

# Or run specific migrations
cd apps/api
alembic upgrade head
```

#### Foreign Key Issues
```sql
-- Check foreign key constraints
SELECT 
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## Configuration Issues

### Environment Variables

**Symptoms:**
- Configuration validation errors
- Missing required variables
- Invalid format errors

**Diagnosis:**
```bash
# Validate configuration
python config_manager.py validate

# Check specific variables
echo $DATABASE_URL
echo $API_PORT
```

**Solutions:**

#### Setup Environment
```bash
# For development
python config_manager.py setup --env development

# For production
python config_manager.py setup --env production

# Validate after setup
python config_manager.py validate
```

#### Fix Specific Variables
```bash
# Example fixes for common issues
export DATABASE_URL="postgresql://studioops:studioops123@localhost:5432/studioops"
export API_HOST="127.0.0.1"
export API_PORT="8003"
```

### .env File Issues

**Symptoms:**
- Variables not loading
- Syntax errors in .env file
- Wrong file location

**Solutions:**

#### Check .env File Location
```bash
# Should be in project root
ls -la .env

# If missing, create from template
cp .env.template .env
```

#### Fix .env Syntax
- No spaces around `=`
- Use quotes for values with spaces
- No leading/trailing whitespace
- Comments start with `#`

Example:
```bash
# Correct
DATABASE_URL=postgresql://user:pass@host:5432/db
API_PORT=8003

# Incorrect
DATABASE_URL = postgresql://user:pass@host:5432/db  # spaces around =
API_PORT = "8003"  # unnecessary quotes for numbers
```

## Performance Issues

### Slow Response Times

**Symptoms:**
- API calls taking too long
- Database queries timing out
- Frontend loading slowly

**Diagnosis:**
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8003/api/health

# Create curl-format.txt:
echo "     time_namelookup:  %{time_namelookup}
        time_connect:  %{time_connect}
     time_appconnect:  %{time_appconnect}
    time_pretransfer:  %{time_pretransfer}
       time_redirect:  %{time_redirect}
  time_starttransfer:  %{time_starttransfer}
                     ----------
          time_total:  %{time_total}" > curl-format.txt
```

**Solutions:**

#### Database Performance
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check database connections
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';
```

#### API Performance
- Check connection pool settings in `.env`
- Monitor memory usage
- Review database query optimization

### Memory Issues

**Symptoms:**
- Out of memory errors
- Application crashes
- Slow garbage collection

**Solutions:**

#### Monitor Memory Usage
```bash
# Check process memory
ps aux | grep python

# On Windows
Get-Process python | Select-Object ProcessName, CPU, WorkingSet
```

#### Optimize Settings
```bash
# Adjust database pool size
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Reduce request limits
API_MAX_REQUEST_SIZE=10485760  # 10MB
```

## Recovery Procedures

### Complete System Reset

If multiple issues persist, follow this complete reset procedure:

#### 1. Stop All Services
```bash
# Stop API server
# Ctrl+C if running in terminal, or kill process

# Stop database (if needed)
Stop-Service postgresql-x64-14

# Stop MinIO (if running locally)
# Ctrl+C or kill process
```

#### 2. Clean Environment
```bash
# Remove existing .env
rm .env

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .pytest_cache/
```

#### 3. Rebuild Environment
```bash
# Set up fresh configuration
python config_manager.py setup --env development

# Validate configuration
python config_manager.py validate

# Install dependencies
pip install -r requirements.txt
```

#### 4. Reset Database
```sql
-- Connect as superuser
psql -h localhost -p 5432 -U postgres

-- Drop and recreate database
DROP DATABASE IF EXISTS studioops;
CREATE DATABASE studioops;
GRANT ALL PRIVILEGES ON DATABASE studioops TO studioops;
```

#### 5. Run Migrations
```bash
# Run database migration
python database_migration_script.py

# Verify schema
python test_startup_validation.py
```

#### 6. Start Services
```bash
# Start PostgreSQL
Start-Service postgresql-x64-14

# Start MinIO (if needed)
minio server C:\minio-data --console-address ":9001"

# Start API server
cd apps/api
python main.py
```

#### 7. Verify System
```bash
# Run full validation
python test_startup_validation.py

# Check services
python config_manager.py check-services

# Test API
curl http://localhost:8003/health
```

## Monitoring and Logs

### Log Locations

- **API Server**: `logs/dev-studioops.log`
- **Database**: PostgreSQL log directory
- **System**: Windows Event Viewer

### Important Log Patterns

#### Error Patterns to Watch
```bash
# API errors
grep -i "error" logs/dev-studioops.log | tail -10

# Database connection issues
grep -i "database" logs/dev-studioops.log | grep -i "error"

# Service degradation
grep -i "degradation" logs/dev-studioops.log
```

#### Performance Monitoring
```bash
# Slow requests
grep -i "slow" logs/dev-studioops.log

# Memory warnings
grep -i "memory" logs/dev-studioops.log

# Connection pool issues
grep -i "pool" logs/dev-studioops.log
```

### Health Check Endpoints

- **API Health**: `GET /health`
- **Database Health**: `GET /health/database`
- **Services Health**: `GET /health/services`

### Monitoring Commands

```bash
# Continuous health monitoring
while true; do
  curl -s http://localhost:8003/health | jq '.status'
  sleep 30
done

# Monitor log file
tail -f logs/dev-studioops.log

# Monitor system resources
Get-Process python | Select-Object ProcessName, CPU, WorkingSet
```

## Getting Help

### Internal Resources

1. **Configuration Validation**: `python config_manager.py validate`
2. **Service Checks**: `python config_manager.py check-services`
3. **Startup Validation**: `python test_startup_validation.py`
4. **System Documentation**: `SYSTEM_FIXES_DOCUMENTATION.md`
5. **Configuration Guide**: `CONFIGURATION.md`

### External Resources

1. **FastAPI Documentation**: https://fastapi.tiangolo.com/
2. **PostgreSQL Documentation**: https://www.postgresql.org/docs/
3. **MinIO Documentation**: https://docs.min.io/
4. **Trello API Documentation**: https://developer.atlassian.com/cloud/trello/
5. **OpenAI API Documentation**: https://platform.openai.com/docs/

### Support Escalation

When escalating issues, include:

1. **System Information**:
   - Operating system and version
   - Python version
   - Package versions (`pip list`)

2. **Configuration**:
   - Environment variables (redact sensitive values)
   - Configuration validation output
   - Service check results

3. **Logs**:
   - Relevant log entries
   - Error messages with full stack traces
   - Timeline of events

4. **Reproduction Steps**:
   - Minimal steps to reproduce the issue
   - Expected vs actual behavior
   - Any workarounds attempted

This comprehensive troubleshooting guide should help diagnose and resolve most common issues with the StudioOps AI system.