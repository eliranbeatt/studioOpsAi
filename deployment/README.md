# StudioOps AI Deployment Scripts

This directory contains deployment scripts and configurations for StudioOps AI.

## Quick Start

### Development Environment

```bash
# 1. Set up configuration
python config_manager.py setup --env development

# 2. Start services
./scripts/start-dev.sh

# 3. Validate system
python test_startup_validation.py
```

### Production Environment

```bash
# 1. Set up configuration
python config_manager.py setup --env production

# 2. Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d

# 3. Validate deployment
./scripts/health-check.sh
```

## Deployment Scripts

- `scripts/start-dev.sh` - Start development environment
- `scripts/start-prod.sh` - Start production environment  
- `scripts/stop-services.sh` - Stop all services
- `scripts/health-check.sh` - Comprehensive health check
- `scripts/backup-database.sh` - Database backup
- `scripts/deploy.sh` - Full deployment script

## Docker Configurations

- `docker-compose.yml` - Development Docker setup
- `docker-compose.prod.yml` - Production Docker setup
- `Dockerfile.api` - API server container
- `Dockerfile.web` - Frontend container

## Configuration Files

- `.env.template` - Configuration template
- `.env.development` - Development configuration
- `.env.production` - Production configuration
- `nginx.conf` - Nginx reverse proxy configuration

## Monitoring and Maintenance

- `monitoring/` - Monitoring configurations
- `scripts/maintenance/` - Regular maintenance scripts
- `scripts/backup/` - Backup and recovery scripts