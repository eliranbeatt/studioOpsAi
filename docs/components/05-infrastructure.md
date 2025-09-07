# Infrastructure Component

## 🐳 Overview

The **Infrastructure Component** provides the complete deployment and operational foundation for StudioOps AI using Docker Compose orchestration. It manages all external services, databases, storage systems, and observability tools required for the platform.

### Purpose and Role in StudioOps AI

The Infrastructure Component serves as the **operational backbone** that:
- Orchestrates all system services through Docker Compose
- Provides PostgreSQL database with vector extensions for AI operations
- Manages object storage through MinIO for document and file handling
- Enables AI observability and monitoring through Langfuse integration
- Handles database migrations, seeding, and schema management
- Supports both development and production deployment scenarios

## 🏗️ Architecture Overview

```mermaid
graph TB
    DevEnv[💻 Development Environment] --> Compose[🐳 Docker Compose]
    Compose --> PostgreSQL[🗄️ PostgreSQL + pgvector]
    Compose --> MinIO[📦 MinIO Object Storage]
    Compose --> Langfuse[📊 Langfuse Observability]
    Compose --> API[🔌 API Container]
    Compose --> Web[🌐 Web Container]
    
    PostgreSQL --> Data[(💾 Persistent Data)]
    MinIO --> Files[(📁 Object Storage)]
    Langfuse --> Traces[(📈 AI Traces)]
    
    API --> PostgreSQL
    API --> MinIO
    API --> Langfuse
    
    Web --> API
    
    Init[🔧 Initialization Scripts] --> PostgreSQL
    Migration[📋 Migration Scripts] --> PostgreSQL
    Seed[🌱 Seed Data] --> PostgreSQL
```

### Key Infrastructure Services

1. **PostgreSQL with pgvector**: Primary database with AI vector extension
2. **MinIO**: S3-compatible object storage for documents and files
3. **Langfuse**: AI observability and LLM operation monitoring
4. **API Container**: Containerized FastAPI backend (optional)
5. **Web Container**: Containerized Next.js frontend (optional)

## 🗄️ Database Infrastructure (PostgreSQL + pgvector)

### **PostgreSQL Configuration**

```yaml
# docker-compose.yaml
postgres:
  image: ankane/pgvector:latest
  container_name: studioops-postgres
  environment:
    POSTGRES_DB: studioops
    POSTGRES_USER: studioops
    POSTGRES_PASSWORD: studioops123
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./init.sql:/docker-entrypoint-initdb.d/init.sql
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U studioops -d studioops"]
    interval: 5s
    timeout: 5s
    retries: 5
```

### **Database Initialization** (`init.sql`)

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create database if not exists
SELECT 'CREATE DATABASE studioops'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'studioops');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE studioops TO studioops;

-- Enable vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_plans_project_id ON plans(project_id);
CREATE INDEX IF NOT EXISTS idx_plan_items_plan_id ON plan_items(plan_id);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_doc_chunks_text_fts ON doc_chunks USING gin(to_tsvector('english', text));
CREATE INDEX IF NOT EXISTS idx_rag_documents_content_fts ON rag_documents USING gin(to_tsvector('english', content));

-- Vector similarity indexes
CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding ON rag_documents USING ivfflat (embedding vector_cosine_ops);
```

### **Database Migration Management**

**Migration Script Structure:**
```python
# infra/migrations/run_migrations.py
import os
import psycopg2
from pathlib import Path

class MigrationRunner:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        self.migrations_dir = Path(__file__).parent
        
    def run_migrations(self):
        """Execute all pending migrations"""
        conn = psycopg2.connect(self.db_url)
        cursor = conn.cursor()
        
        try:
            # Create migrations table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL UNIQUE,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get executed migrations
            cursor.execute("SELECT filename FROM migrations")
            executed = {row[0] for row in cursor.fetchall()}
            
            # Run pending migrations
            migration_files = sorted(self.migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                if migration_file.name not in executed:
                    print(f"Running migration: {migration_file.name}")
                    
                    with open(migration_file, 'r') as f:
                        cursor.execute(f.read())
                    
                    cursor.execute(
                        "INSERT INTO migrations (filename) VALUES (%s)",
                        (migration_file.name,)
                    )
                    conn.commit()
                    
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    runner = MigrationRunner()
    runner.run_migrations()
```

**Sample Migration Files:**
```sql
-- infra/migrations/001_initial_schema.sql
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- infra/migrations/002_add_vector_support.sql
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE rag_documents 
ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding 
ON rag_documents USING ivfflat (embedding vector_cosine_ops);
```

## 📦 Object Storage Infrastructure (MinIO)

### **MinIO Configuration**

```yaml
# docker-compose.yaml
minio:
  image: minio/minio:latest
  container_name: studioops-minio
  ports:
    - "9000:9000"    # API port
    - "9001:9001"    # Console port
  environment:
    MINIO_ROOT_USER: studioops
    MINIO_ROOT_PASSWORD: studioops123
  command: server /data --console-address ":9001"
  volumes:
    - minio_data:/data
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 30s
    timeout: 20s
    retries: 3
```

### **MinIO Initialization Script**

```bash
#!/bin/bash
# infra/minio-init.sh

# Wait for MinIO to be ready
until curl -f http://localhost:9000/minio/health/live; do
  echo "Waiting for MinIO to be ready..."
  sleep 2
done

# Install MinIO client
curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Configure MinIO client
mc alias set local http://localhost:9000 studioops studioops123

# Create required buckets
mc mb local/documents
mc mb local/uploads
mc mb local/generated
mc mb local/backups

# Set bucket policies
mc policy set public local/uploads
mc policy set private local/documents
mc policy set private local/generated

echo "MinIO initialization complete"
```

### **Bucket Structure**

```
studioops-minio/
├── documents/          # Processed documents
│   ├── projects/       # Project-specific documents
│   ├── quotes/         # Quote documents
│   └── invoices/       # Invoice documents
├── uploads/            # Temporary upload storage
│   └── pending/        # Files awaiting processing
├── generated/          # Generated content
│   ├── reports/        # Generated reports
│   └── pdfs/           # Generated PDF files
└── backups/            # Database and file backups
    ├── daily/          # Daily backups
    └── weekly/         # Weekly backups
```

## 📊 Observability Infrastructure (Langfuse)

### **Langfuse Configuration**

```yaml
# docker-compose.yaml
langfuse:
  image: langfuse/langfuse:latest
  container_name: studioops-langfuse
  ports:
    - "3100:3000"
  environment:
    DATABASE_URL: postgresql://studioops:studioops@postgres:5432/studioops
    NEXTAUTH_SECRET: your-secret-here
    NEXTAUTH_URL: http://localhost:3100
    LANGFUSE_SECRET: your-langfuse-secret
  depends_on:
    postgres:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:3000/api/public/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### **Langfuse Integration Setup**

**Environment Variables:**
```bash
# API Backend configuration
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://localhost:3100

# Frontend configuration (optional)
NEXT_PUBLIC_LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
```

**API Backend Integration:**
```python
# apps/api/services/observability_service.py
from langfuse import Langfuse

class ObservabilityService:
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
            secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
            host=os.getenv('LANGFUSE_HOST', 'http://localhost:3100')
        )
        self.enabled = bool(os.getenv('LANGFUSE_PUBLIC_KEY'))
        
    def trace_llm_call(self, trace_id: str, input_text: str, output_text: str, model: str):
        """Track LLM API calls with performance metrics"""
        if not self.enabled:
            return
            
        self.langfuse.generation(
            id=f"{trace_id}-generation",
            trace_id=trace_id,
            name="llm_generation",
            model=model,
            input=input_text,
            output=output_text,
            usage={
                "input_tokens": len(input_text.split()),
                "output_tokens": len(output_text.split())
            }
        )
```

## 🔄 Container Orchestration

### **Docker Compose Configuration** (`docker-compose.yaml`)

```yaml
version: '3.8'

services:
  # Database with vector extensions
  postgres:
    image: ankane/pgvector:latest
    container_name: studioops-postgres
    environment:
      POSTGRES_DB: studioops
      POSTGRES_USER: studioops
      POSTGRES_PASSWORD: studioops123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U studioops -d studioops"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Object storage
  minio:
    image: minio/minio:latest
    container_name: studioops-minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: studioops
      MINIO_ROOT_PASSWORD: studioops123
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # AI observability
  langfuse:
    image: langfuse/langfuse:latest
    container_name: studioops-langfuse
    ports:
      - "3100:3000"
    environment:
      DATABASE_URL: postgresql://studioops:studioops@postgres:5432/studioops
      NEXTAUTH_SECRET: your-secret-here
      NEXTAUTH_URL: http://localhost:3100
      LANGFUSE_SECRET: your-langfuse-secret
    depends_on:
      postgres:
        condition: service_healthy

  # Optional: API container for production
  api:
    build:
      context: ../apps/api
      dockerfile: Dockerfile
    container_name: studioops-api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://studioops:studioops123@postgres:5432/studioops
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: studioops
      MINIO_SECRET_KEY: studioops123
      LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:-pk-lf-}
      LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY:-sk-lf-}
      LANGFUSE_HOST: http://langfuse:3000
    volumes:
      - ../apps/api:/app
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy

  # Optional: Web container for production
  web:
    build:
      context: ../apps/web
      dockerfile: Dockerfile
    container_name: studioops-web
    ports:
      - "3200:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:-pk-lf-}
    volumes:
      - ../apps/web:/app
      - /app/node_modules
    depends_on:
      - api

# Persistent volumes
volumes:
  postgres_data:
  minio_data:
```

## 🛠️ Management Commands (Makefile)

### **Infrastructure Management**

```makefile
# Makefile
.PHONY: dev-up dev-down db-migrate db-seed api web logs health

# Start all infrastructure services
dev-up:
	docker-compose -f infra/docker-compose.yaml up -d
	@echo "Infrastructure services started"
	@echo "PostgreSQL: localhost:5432"
	@echo "MinIO: http://localhost:9000 (Console: http://localhost:9001)"
	@echo "Langfuse: http://localhost:3100"

# Stop all services
dev-down:
	docker-compose -f infra/docker-compose.yaml down
	@echo "Infrastructure services stopped"

# Run database migrations
db-migrate:
	python infra/migrations/run_migrations.py
	@echo "Database migrations completed"

# Seed database with sample data
db-seed:
	cd packages/db && python seed.py
	@echo "Database seeded with sample data"

# Start API server (local development)
api:
	cd apps/api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start web server (local development)
web:
	cd apps/web && pnpm dev

# View service logs
logs:
	docker-compose -f infra/docker-compose.yaml logs -f

# Check service health
health:
	docker-compose -f infra/docker-compose.yaml ps
	@echo "\nHealth Checks:"
	@curl -s http://localhost:5432 > /dev/null && echo "✅ PostgreSQL: Connected" || echo "❌ PostgreSQL: Not responding"
	@curl -s http://localhost:9000/minio/health/live > /dev/null && echo "✅ MinIO: Healthy" || echo "❌ MinIO: Not responding"
	@curl -s http://localhost:3100/api/public/health > /dev/null && echo "✅ Langfuse: Healthy" || echo "❌ Langfuse: Not responding"

# Backup database
backup-db:
	docker exec studioops-postgres pg_dump -U studioops studioops > backup_$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backup created"

# Restore database
restore-db:
	@read -p "Enter backup file path: " BACKUP_FILE; \
	docker exec -i studioops-postgres psql -U studioops studioops < $$BACKUP_FILE
	@echo "Database restored"

# Clean up volumes (DANGEROUS - removes all data)
clean:
	@read -p "This will remove all data. Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker-compose -f infra/docker-compose.yaml down -v; \
		docker volume prune -f; \
		echo "All data removed"; \
	else \
		echo "Operation cancelled"; \
	fi
```

## 🔧 Environment Configuration

### **Development Environment**

```bash
# .env.development
DATABASE_URL=postgresql://studioops:studioops123@localhost:5432/studioops
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=studioops
MINIO_SECRET_KEY=studioops123
LANGFUSE_PUBLIC_KEY=pk-lf-development-key
LANGFUSE_SECRET_KEY=sk-lf-development-secret
LANGFUSE_HOST=http://localhost:3100
```

### **Production Environment**

```bash
# .env.production
DATABASE_URL=postgresql://prod_user:secure_password@prod-db:5432/studioops_prod
MINIO_ENDPOINT=prod-minio:9000
MINIO_ACCESS_KEY=prod_access_key
MINIO_SECRET_KEY=secure_secret_key
LANGFUSE_PUBLIC_KEY=pk-lf-production-key
LANGFUSE_SECRET_KEY=sk-lf-production-secret
LANGFUSE_HOST=https://langfuse.yourdomain.com
```

## 🚀 Deployment Scenarios

### **Development Deployment**

```bash
# Quick development setup
make dev-up
make db-migrate
make db-seed

# Start local servers
make api    # Terminal 1
make web    # Terminal 2
```

### **Staging Deployment**

```bash
# Start infrastructure
docker-compose -f infra/docker-compose.yaml up -d

# Build and start application containers
docker-compose -f infra/docker-compose.yaml up -d api web

# Run migrations
make db-migrate
```

### **Production Deployment**

```yaml
# docker-compose.prod.yaml
version: '3.8'
services:
  postgres:
    image: ankane/pgvector:latest
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - studioops-network

  api:
    image: studioops/api:latest
    restart: unless-stopped
    environment:
      DATABASE_URL: ${DATABASE_URL}
      MINIO_ENDPOINT: ${MINIO_ENDPOINT}
    depends_on:
      - postgres
    networks:
      - studioops-network

networks:
  studioops-network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
```

## 🔍 Monitoring and Health Checks

### **Service Health Monitoring**

```python
# Health check endpoints
async def check_infrastructure_health():
    """Comprehensive infrastructure health check"""
    health_status = {
        "database": await check_database_health(),
        "minio": await check_minio_health(),
        "langfuse": await check_langfuse_health(),
        "overall": "healthy"
    }
    
    # Determine overall health
    if any(service["status"] != "healthy" for service in health_status.values() if isinstance(service, dict)):
        health_status["overall"] = "degraded"
    
    return health_status

async def check_database_health():
    """Check PostgreSQL database connectivity"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy" if result and result[0] == 1 else "unhealthy",
            "service": "postgresql",
            "details": {"connection": "successful"}
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "postgresql",
            "error": str(e)
        }
```

### **Performance Monitoring**

```python
# Resource usage monitoring
def get_infrastructure_metrics():
    """Get infrastructure performance metrics"""
    return {
        "database": {
            "connections": get_db_connection_count(),
            "size": get_db_size(),
            "queries_per_second": get_db_qps()
        },
        "storage": {
            "minio_usage": get_minio_usage(),
            "disk_space": get_disk_usage()
        },
        "observability": {
            "traces_count": get_langfuse_traces_count(),
            "error_rate": get_error_rate()
        }
    }
```

## 🔒 Security and Backup

### **Security Configuration**

```yaml
# Security best practices
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /var/tmp
user: "1000:1000"
cap_drop:
  - ALL
cap_add:
  - CHOWN
  - DAC_OVERRIDE
```

### **Backup Strategy**

```bash
#!/bin/bash
# backup.sh - Automated backup script

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker exec studioops-postgres pg_dump -U studioops studioops > "${BACKUP_DIR}/db_backup_${DATE}.sql"

# MinIO backup
docker exec studioops-minio mc mirror /data "${BACKUP_DIR}/minio_backup_${DATE}/"

# Compress backups
tar -czf "${BACKUP_DIR}/full_backup_${DATE}.tar.gz" "${BACKUP_DIR}/*_backup_${DATE}*"

# Clean old backups (keep last 7 days)
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: full_backup_${DATE}.tar.gz"
```

## 📋 Troubleshooting

### **Common Issues**

**Services won't start:**
```bash
# Check Docker daemon
systemctl status docker

# Check port conflicts
netstat -tulpn | grep :5432
netstat -tulpn | grep :9000

# Check logs
docker-compose logs postgres
docker-compose logs minio
```

**Database connection issues:**
```bash
# Test database connectivity
docker exec studioops-postgres psql -U studioops -d studioops -c "SELECT 1;"

# Check database permissions
docker exec studioops-postgres psql -U studioops -d studioops -c "\du"
```

**Storage issues:**
```bash
# Check MinIO status
curl http://localhost:9000/minio/health/live

# Check available space
df -h

# Restart MinIO
docker restart studioops-minio
```

The Infrastructure Component provides a robust, scalable foundation for StudioOps AI with comprehensive service orchestration, monitoring, and management capabilities essential for both development and production environments.