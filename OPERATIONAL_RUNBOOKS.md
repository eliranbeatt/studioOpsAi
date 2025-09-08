# StudioOps AI Operational Runbooks

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Weekly Maintenance](#weekly-maintenance)
3. [Monthly Reviews](#monthly-reviews)
4. [Incident Response](#incident-response)
5. [Backup and Recovery](#backup-and-recovery)
6. [Performance Monitoring](#performance-monitoring)
7. [Security Maintenance](#security-maintenance)
8. [Capacity Planning](#capacity-planning)

## Daily Operations

### Morning Health Check (5 minutes)

**Frequency**: Every business day at 9:00 AM

**Checklist**:
1. ✅ Run system health validation
2. ✅ Check service connectivity
3. ✅ Review overnight logs
4. ✅ Verify database connectivity
5. ✅ Check external service status

**Commands**:
```bash
# System health check
python test_startup_validation.py

# Service connectivity
python config_manager.py check-services

# Review logs (last 24 hours)
grep -i "error\|critical\|fatal" logs/dev-studioops.log | tail -20

# Database status
psql -h localhost -p 5432 -U studioops -d studioops -c "SELECT version();"

# API endpoint check
curl -s http://localhost:8003/health | jq '.'
```

**Expected Results**:
- System health: ✅ Startup successful
- Service connectivity: 2/4 or 4/4 services accessible
- No critical errors in logs
- Database responds within 5 seconds
- API health endpoint returns 200 OK

**Escalation**: If any check fails, follow [Incident Response](#incident-response) procedure.

### Evening Log Review (10 minutes)

**Frequency**: Every business day at 6:00 PM

**Checklist**:
1. ✅ Review daily error logs
2. ✅ Check performance metrics
3. ✅ Verify backup completion
4. ✅ Monitor resource usage

**Commands**:
```bash
# Daily error summary
grep -i "error" logs/dev-studioops.log | grep "$(date +%Y-%m-%d)" | wc -l

# Performance check
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8003/api/health

# Resource usage (Windows)
Get-Process python | Select-Object ProcessName, CPU, WorkingSet

# Disk space check
Get-PSDrive C | Select-Object Used, Free
```

**Thresholds**:
- Daily errors: < 10 acceptable, > 20 investigate
- API response time: < 500ms normal, > 2000ms investigate
- Memory usage: < 2GB normal, > 4GB investigate
- Disk free space: > 10GB acceptable, < 5GB critical

## Weekly Maintenance

### Monday: Configuration Audit (15 minutes)

**Tasks**:
1. Review and validate configuration
2. Check for configuration drift
3. Update environment documentation
4. Verify security settings

**Commands**:
```bash
# Configuration validation
python config_manager.py validate

# Generate fresh documentation
python config_manager.py generate-docs

# Security audit
python -c "
import os
sensitive_vars = ['OPENAI_API_KEY', 'TRELLO_API_TOKEN', 'JWT_SECRET_KEY']
for var in sensitive_vars:
    value = os.getenv(var, 'NOT_SET')
    if value == 'NOT_SET':
        print(f'⚠️  {var}: Not configured')
    elif len(value) < 16:
        print(f'⚠️  {var}: Potentially weak')
    else:
        print(f'✅ {var}: Configured')
"
```

### Wednesday: Database Maintenance (20 minutes)

**Tasks**:
1. Run database health checks
2. Analyze query performance
3. Check foreign key constraints
4. Review database size and growth

**Commands**:
```bash
# Database health
psql -h localhost -p 5432 -U studioops -d studioops << EOF
-- Connection count
SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';

-- Database size
SELECT pg_size_pretty(pg_database_size('studioops')) as db_size;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Foreign key constraints check
SELECT 
    tc.table_name,
    tc.constraint_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public';
EOF
```

### Friday: Performance Review (25 minutes)

**Tasks**:
1. Analyze weekly performance trends
2. Review error patterns
3. Check resource utilization
4. Plan capacity adjustments

**Performance Analysis**:
```bash
# Weekly error analysis
echo "Error Summary for $(date -d '7 days ago' +%Y-%m-%d) to $(date +%Y-%m-%d):"
for day in {0..6}; do
    day_date=$(date -d "$day days ago" +%Y-%m-%d)
    error_count=$(grep -c "$day_date.*ERROR" logs/dev-studioops.log 2>/dev/null || echo 0)
    echo "$day_date: $error_count errors"
done

# Response time analysis
echo "Testing API response times..."
for endpoint in health api/projects api/documents; do
    echo -n "$endpoint: "
    curl -w "%{time_total}s\n" -o /dev/null -s http://localhost:8003/$endpoint
done
```

## Monthly Reviews

### First Monday: Security Review (45 minutes)

**Tasks**:
1. Review API key rotation status
2. Check for security vulnerabilities
3. Audit user access and permissions
4. Review security logs

**Security Checklist**:
```bash
# Check API key ages (manual review required)
echo "Review API key creation dates:"
echo "- OpenAI API key: Check https://platform.openai.com/api-keys"
echo "- Trello API token: Check https://trello.com/app-key"

# Configuration security review
python -c "
import os
config_issues = []

# Check development mode in production
if os.getenv('DEVELOPMENT_MODE', '').lower() == 'true':
    config_issues.append('DEVELOPMENT_MODE is enabled')

if os.getenv('DEBUG_ENABLED', '').lower() == 'true':
    config_issues.append('DEBUG_ENABLED is enabled')

# Check JWT secret strength
jwt_secret = os.getenv('JWT_SECRET_KEY', '')
if 'dev' in jwt_secret.lower() or 'test' in jwt_secret.lower():
    config_issues.append('JWT_SECRET_KEY appears to be a development key')

if config_issues:
    print('🔒 Security Issues Found:')
    for issue in config_issues:
        print(f'  - {issue}')
else:
    print('✅ No security configuration issues found')
"
```

### Mid-Month: Capacity Planning (30 minutes)

**Tasks**:
1. Analyze resource usage trends
2. Review database growth
3. Plan for scaling requirements
4. Update capacity recommendations

**Capacity Analysis**:
```bash
# Database growth analysis
psql -h localhost -p 5432 -U studioops -d studioops << EOF
SELECT 
    'Total DB Size' as metric,
    pg_size_pretty(pg_database_size('studioops')) as current_size;

SELECT 
    'Largest Tables' as category,
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC
LIMIT 5;
EOF

# Projected storage needs (manual calculation)
echo "Manual Review Required:"
echo "1. Estimate monthly data growth"
echo "2. Calculate 6-month storage projection"
echo "3. Review backup storage requirements"
echo "4. Plan for traffic growth"
```

## Incident Response

### Severity Levels

**P1 - Critical (15 minutes response)**:
- System completely down
- Data loss occurring
- Security breach

**P2 - High (1 hour response)**:
- Major functionality impaired
- Multiple users affected
- External service failures

**P3 - Medium (4 hours response)**:
- Minor functionality issues
- Single user affected
- Performance degradation

**P4 - Low (24 hours response)**:
- Cosmetic issues
- Enhancement requests
- Documentation updates

### Incident Response Procedures

#### P1 - Critical Incident

1. **Immediate Actions (0-5 minutes)**:
   ```bash
   # Quick health check
   python test_startup_validation.py
   
   # Check if services are running
   python config_manager.py check-services
   
   # Check API server
   curl -s http://localhost:8003/health
   ```

2. **Diagnosis (5-10 minutes)**:
   ```bash
   # Check recent errors
   tail -50 logs/dev-studioops.log | grep -i "error\|critical\|fatal"
   
   # Check database connectivity
   pg_isready -h localhost -p 5432 -U studioops
   
   # Check system resources
   Get-Process python | Select-Object ProcessName, CPU, WorkingSet
   ```

3. **Resolution Actions (10-15 minutes)**:
   - Restart failed services
   - Restore from backup if data loss
   - Implement emergency fallbacks
   - Communicate with stakeholders

#### P2 - High Priority Incident

1. **Assessment (0-15 minutes)**:
   - Identify affected components
   - Estimate user impact
   - Check for workarounds

2. **Investigation (15-45 minutes)**:
   - Analyze logs for root cause
   - Test affected functionality
   - Check external service status

3. **Resolution (45-60 minutes)**:
   - Implement fix or workaround
   - Test solution
   - Monitor for regression

### Emergency Contacts

```
Primary On-Call: [Your Name] - [Phone] - [Email]
Secondary: [Backup Name] - [Phone] - [Email]
Database Admin: [DBA Name] - [Phone] - [Email]
External Service Support:
  - OpenAI: https://help.openai.com/
  - Trello: https://help.trello.com/
```

## Backup and Recovery

### Daily Backups (Automated)

**Database Backup**:
```bash
#!/bin/bash
# daily-backup.sh

BACKUP_DIR="/var/backups/studioops"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="studioops"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -p 5432 -U studioops $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# MinIO data backup (if local)
if [ -d "./minio-data" ]; then
    tar -czf $BACKUP_DIR/minio_backup_$DATE.tar.gz ./minio-data
fi

# Configuration backup
cp .env $BACKUP_DIR/env_backup_$DATE.txt

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.txt" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### Recovery Procedures

**Database Recovery**:
```bash
# 1. Stop API server
pkill -f "uvicorn main:app"

# 2. Drop and recreate database
psql -h localhost -p 5432 -U postgres << EOF
DROP DATABASE IF EXISTS studioops;
CREATE DATABASE studioops;
GRANT ALL PRIVILEGES ON DATABASE studioops TO studioops;
EOF

# 3. Restore from backup
gunzip -c /var/backups/studioops/db_backup_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -p 5432 -U studioops studioops

# 4. Restart API server
cd apps/api
uvicorn main:app --host 127.0.0.1 --port 8003 &
```

## Performance Monitoring

### Key Metrics

**Response Time Targets**:
- API Health endpoint: < 100ms
- Database queries: < 500ms
- File operations: < 2s
- AI service calls: < 30s

**Resource Limits**:
- CPU usage: < 80%
- Memory usage: < 4GB
- Disk usage: < 80%
- Database connections: < 50

### Monitoring Commands

```bash
# API performance test
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8003/health

# Database performance
psql -h localhost -p 5432 -U studioops -d studioops -c "
SELECT 
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# System resources
Get-Process python | Select-Object ProcessName, CPU, WorkingSet
Get-Counter "\Memory\Available MBytes"
Get-Counter "\Processor(_Total)\% Processor Time"
```

## Security Maintenance

### Monthly Security Tasks

1. **API Key Rotation** (Quarterly):
   ```bash
   # Check API key ages and rotate if needed
   echo "1. Generate new OpenAI API key"
   echo "2. Generate new Trello API token"
   echo "3. Update .env file"
   echo "4. Restart services"
   echo "5. Test functionality"
   ```

2. **Security Scanning**:
   ```bash
   # Check for known vulnerabilities
   pip audit
   
   # Configuration security check
   python config_manager.py validate | grep -i "critical\|error"
   ```

3. **Access Review**:
   - Review user accounts and permissions
   - Check API access logs
   - Validate service account credentials

### Security Incident Response

**Data Breach**:
1. Immediately rotate all API keys
2. Check logs for unauthorized access
3. Notify stakeholders
4. Implement additional security measures

**Suspicious Activity**:
1. Monitor API access patterns
2. Check for unusual database queries
3. Review authentication logs
4. Implement rate limiting if needed

## Capacity Planning

### Growth Projections

**Monthly Review Items**:
- Database size growth rate
- API request volume trends
- File storage usage patterns
- User activity patterns

**Scaling Triggers**:
- Database size > 10GB: Consider optimization
- API response time > 2s: Scale API servers
- Memory usage > 6GB: Increase server resources
- Error rate > 5%: Investigate and optimize

### Resource Planning

**Short-term (1-3 months)**:
- Monitor current usage patterns
- Plan for 20% growth
- Identify bottlenecks

**Medium-term (3-6 months)**:
- Evaluate infrastructure scaling
- Consider service optimization
- Plan for feature expansion

**Long-term (6-12 months)**:
- Architectural improvements
- Microservices migration
- Advanced monitoring implementation

This operational runbook provides comprehensive procedures for maintaining the StudioOps AI system's reliability, security, and performance.