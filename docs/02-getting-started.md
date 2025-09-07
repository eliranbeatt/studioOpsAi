# Getting Started with StudioOps AI

## 🚀 Quick Start Guide for Developers

This guide will help you set up a complete development environment for StudioOps AI and understand the basic development workflow.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software
- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Python** (3.9+) with pip
- **Node.js** (16+) with npm/pnpm
- **Git** for version control
- **Code Editor** (VS Code recommended)

### Optional but Recommended
- **Python virtual environment manager** (venv, conda, or pyenv)
- **Chrome/Chromium browser** (for DevTools MCP integration)
- **Postman or similar** (for API testing)

## 🛠️ Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd claude-code
```

### 2. Environment Configuration

Create environment files from examples:

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables as needed
nano .env
```

**Key Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://studioops:studioops123@localhost:5432/studioops

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# AI Services (Optional for basic development)
OPENAI_API_KEY=your_openai_key_here
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key

# MinIO Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=studioops
MINIO_SECRET_KEY=studioops123
```

### 3. Infrastructure Setup

Start the required services using Docker Compose:

```bash
# Start all infrastructure services
make dev-up

# Or manually with docker-compose
docker-compose -f infra/docker-compose.yaml up -d
```

This starts:
- **PostgreSQL** with pgvector (port 5432)
- **MinIO** object storage (port 9000, console: 9001)
- **Langfuse** observability (port 3100)

### 4. Database Setup

Initialize the database with schema and seed data:

```bash
# Run database migrations
make db-migrate

# Seed with sample data
make db-seed
```

### 5. Backend API Setup

```bash
# Navigate to API directory
cd apps/api

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the Makefile
make api
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/redoc

### 6. Frontend Web App Setup

Open a new terminal window:

```bash
# Navigate to web app directory
cd apps/web

# Install dependencies
npm install
# or if you prefer pnpm
pnpm install

# Start development server
npm run dev

# Or use the Makefile
make web
```

The web application will be available at:
- **Web App**: http://localhost:3000

### 7. SuperClaude Framework Setup (Optional)

For AI features and agent capabilities:

```bash
# Navigate to SuperClaude Framework
cd SuperClaude_Framework

# Install SuperClaude (if not already installed globally)
pip install -e .

# Or install via npm
npm install -g @bifrost_inc/superclaude

# Install framework
superclaude install
```

### 8. Chrome DevTools MCP Setup (Optional)

For browser debugging integration:

```bash
# Navigate to Chrome DevTools MCP
cd chrome-devtools-mcp

# Install dependencies
pip install -r requirements.txt

# The MCP server will be available for Claude Desktop integration
```

## 🚀 Quick Development Workflow

### Using Provided Scripts

The project includes convenience scripts for rapid development:

**Windows:**
```cmd
# Command Prompt
run_dev.bat

# PowerShell
.\run_dev.ps1
```

**Linux/Mac:**
```bash
chmod +x run_dev.sh
./run_dev.sh
```

These scripts will:
1. Start all infrastructure services
2. Set up the API server
3. Start the web development server
4. Display service URLs and status

### Manual Development Workflow

1. **Start Infrastructure** (once per session):
   ```bash
   make dev-up
   ```

2. **Start API Backend** (terminal 1):
   ```bash
   cd apps/api
   source venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start Web Frontend** (terminal 2):
   ```bash
   cd apps/web
   npm run dev
   ```

4. **Develop and Test** 🎉

## 🔍 Verifying Your Setup

### Health Checks

1. **Infrastructure Services:**
   ```bash
   # Check service status
   make health
   
   # View service logs
   make logs
   ```

2. **API Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status": "healthy", "database": "connected", "service": "studioops-api"}`

3. **Web Application:**
   Visit http://localhost:3000 - you should see the StudioOps AI dashboard

4. **Database Connection:**
   ```bash
   # Connect to database (optional)
   docker exec -it studioops-postgres psql -U studioops -d studioops
   ```

### Testing the System

1. **API Tests:**
   ```bash
   cd apps/api
   pytest
   ```

2. **Frontend Tests:**
   ```bash
   cd apps/web
   npm test
   ```

3. **E2E Tests:**
   ```bash
   cd apps/web
   npm run test:e2e
   ```

## 📁 Project Structure Overview

```
claude-code/
├── 📁 SuperClaude_Framework/    # AI agent system
├── 📁 apps/
│   ├── 📁 api/                  # FastAPI backend
│   └── 📁 web/                  # Next.js frontend
├── 📁 chrome-devtools-mcp/      # Browser debugging
├── 📁 infra/                    # Docker & infrastructure
├── 📁 packages/                 # Shared libraries
├── 📁 docs/                     # This documentation
├── 📄 Makefile                  # Development commands
├── 📄 docker-compose.yml        # Backup compose file
└── 📄 run_dev.*                 # Quick start scripts
```

## 🎯 Development Workflow

### Day-to-Day Development

1. **Start your development session:**
   ```bash
   # Start infrastructure if not running
   make dev-up
   
   # Start API and Web servers
   ./run_dev.sh  # or run_dev.bat on Windows
   ```

2. **Make changes:**
   - **Backend changes**: Edit files in `apps/api/`, server auto-reloads
   - **Frontend changes**: Edit files in `apps/web/src/`, browser auto-refreshes
   - **Database changes**: Update models in `apps/api/models.py` and run migrations

3. **Test your changes:**
   ```bash
   # Test API
   curl http://localhost:8000/health
   
   # Test frontend
   # Visit http://localhost:3000 in browser
   
   # Run automated tests
   cd apps/api && pytest
   cd apps/web && npm test
   ```

4. **Database updates:**
   ```bash
   # After model changes, run migrations
   make db-migrate
   ```

### Common Development Tasks

**Adding a new API endpoint:**
1. Create/edit router in `apps/api/routers/`
2. Add business logic in `apps/api/services/`
3. Update data models in `apps/api/models.py` if needed
4. Include router in `apps/api/main.py`

**Adding a frontend component:**
1. Create component in `apps/web/src/components/`
2. Add to appropriate page in `apps/web/src/app/`
3. Update types in `apps/web/src/types/` if needed

**Working with the database:**
```bash
# Reset database to clean state
make dev-down && make dev-up && make db-migrate && make db-seed

# Connect to database
docker exec -it studioops-postgres psql -U studioops -d studioops
```

## 🔧 Troubleshooting

### Common Issues

**Docker services won't start:**
```bash
# Check Docker is running
docker --version

# Check for port conflicts
docker ps
netstat -an | grep 5432  # PostgreSQL
netstat -an | grep 3000  # Web app
netstat -an | grep 8000  # API
```

**API won't start:**
```bash
# Check Python environment
python --version
pip list | grep fastapi

# Check database connection
docker logs studioops-postgres
```

**Frontend won't start:**
```bash
# Check Node.js environment
node --version
npm --version

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Database connection issues:**
```bash
# Restart database
docker restart studioops-postgres

# Check database logs
docker logs studioops-postgres

# Verify environment variables
echo $DATABASE_URL
```

### Getting Help

1. Check the [Troubleshooting Guide](reference/troubleshooting.md)
2. Review component-specific documentation
3. Check service logs: `make logs`
4. Verify environment variables and configuration

## 🎯 Next Steps

Once you have the system running:

1. **Explore the API**: Visit http://localhost:8000/docs to see all available endpoints
2. **Use the Web Interface**: Navigate through the project management features at http://localhost:3000
3. **Read Component Documentation**: Start with [API Backend](components/02-api-backend.md) and [Web Frontend](components/03-web-frontend.md)
4. **Set up AI Features**: Configure [SuperClaude Framework](components/01-superclaude-framework.md) for AI capabilities
5. **Try Browser Debugging**: Set up [Chrome DevTools MCP](components/04-chrome-devtools-mcp.md)

## 🚀 Ready to Develop!

You now have a fully functional StudioOps AI development environment. The system is designed for rapid development with hot reloading, comprehensive testing, and modular architecture.

**Happy coding!** 🎉