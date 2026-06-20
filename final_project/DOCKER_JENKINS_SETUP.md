# Docker and Jenkins CI/CD Documentation

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Docker Setup](#docker-setup)
4. [Docker Compose Setup](#docker-compose-setup)
5. [Jenkins Setup](#jenkins-setup)
6. [Jenkins Pipeline Configuration](#jenkins-pipeline-configuration)
7. [Environment Configuration](#environment-configuration)
8. [Running the Application](#running-the-application)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

## Overview

This project uses Docker for containerization and Jenkins for continuous integration and continuous deployment (CI/CD). The setup includes:

- **Backend**: FastAPI application running in a Docker container
- **Frontend**: React application (Vite) running in a Docker container
- **Database**: Oracle Database running in a Docker container
- **Orchestration**: Docker Compose for managing all services
- **CI/CD Pipeline**: Jenkins pipeline for automated testing, building, and deployment

## Prerequisites

### Required Software
- Docker Desktop (version 20.10+)
- Docker Compose (version 2.0+)
- Jenkins (version 2.350+)
- Git (version 2.30+)
- Python 3.11+ (for backend development)
- Node.js 20+ (for frontend development)

### System Requirements
- Minimum 8GB RAM
- 20GB free disk space
- Docker with at least 4GB memory allocation

### Docker Installation
```bash
# Windows (WSL 2)
# Download Docker Desktop from https://www.docker.com/products/docker-desktop

# Linux (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify installation
docker --version
docker-compose --version
```

## Docker Setup

### Backend Dockerfile

The backend Dockerfile uses multi-stage builds for optimization:

```dockerfile
# Stage 1: Builder - Compiles dependencies
# Stage 2: Runtime - Minimal production image

# Key Features:
- Python 3.11 slim base image
- Oracle connectivity libraries
- Health checks
- Non-root user execution (recommended)
- Minimal final image size
```

**Build Command:**
```bash
cd backend_fastapi
docker build -t job-portal-backend:latest .
```

**Run Standalone (for testing):**
```bash
docker run -d \
  --name backend \
  -p 8000:8000 \
  -e ORACLE_USER=narasimha \
  -e ORACLE_PASSWORD=narasimha \
  -e ORACLE_HOST=oracle-db \
  -e ORACLE_PORT=1521 \
  -e ORACLE_SERVICE=XE \
  job-portal-backend:latest
```

### Frontend Dockerfile

The frontend Dockerfile also uses multi-stage builds:

```dockerfile
# Stage 1: Builder - Builds the React application
# Stage 2: Runtime - Serves the built application

# Key Features:
- Node.js 20 alpine base image
- Vite build optimization
- Serve package for production serving
- Health checks
- Minimal final image size (~200MB)
```

**Build Command:**
```bash
cd goskill-frontend
docker build -t job-portal-frontend:latest .
```

**Run Standalone (for testing):**
```bash
docker run -d \
  --name frontend \
  -p 3000:3000 \
  -e VITE_API_URL=http://localhost:8000 \
  job-portal-frontend:latest
```

### .dockerignore Files

Both Dockerfiles include `.dockerignore` files to exclude unnecessary files from the build context:

**Backend excludes:**
- Git files (.git, .gitignore)
- IDE files (.vscode, .idea)
- Virtual environments (venv, venv99)
- Test files and coverage reports
- Environment files (.env)

**Frontend excludes:**
- Git files
- IDE files
- node_modules (reinstalled during build)
- Environment files
- Build artifacts from previous builds

## Docker Compose Setup

### docker-compose.yml Overview

The `docker-compose.yml` orchestrates three main services:

1. **Oracle Database Service**
   - Image: `container-registry.oracle.com/database/enterprise:latest`
   - Port: 1521 (configurable)
   - Volume: `oracle-data` for persistent storage
   - Health checks enabled
   - Initialization time: ~2 minutes

2. **Backend Service**
   - Depends on: Oracle Database
   - Port: 8000
   - Environment: Oracle connection variables
   - Volume: Resume uploads storage
   - Health checks: 30-second interval

3. **Frontend Service**
   - Depends on: Backend Service
   - Port: 3000
   - Environment: API URL configuration
   - Health checks: 30-second interval

### Docker Compose Commands

**Starting the Application:**
```bash
# Start all services in background
docker-compose up -d

# Start with custom environment file
docker-compose --env-file .env.production up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f oracle-db
```

**Stopping the Application:**
```bash
# Stop all services (preserves volumes)
docker-compose stop

# Stop and remove containers (preserves volumes)
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v

# Remove specific service
docker-compose rm backend
```

**Checking Service Status:**
```bash
# List all containers
docker-compose ps

# Check service health
docker-compose logs oracle-db | tail -20

# Inspect service
docker-compose exec backend curl http://localhost:8000/docs
```

**Building and Running:**
```bash
# Build images without starting
docker-compose build

# Build and start
docker-compose up -d --build

# Force rebuild (no cache)
docker-compose build --no-cache
docker-compose up -d
```

## Environment Configuration

### Creating Environment Files

**Development Environment (.env.development):**
```bash
cp .env.example .env.development

# Edit with development settings
ORACLE_PASSWORD=dev_password
VITE_API_URL=http://localhost:8000
APP_DEBUG=true
```

**Production Environment (.env.production):**
```bash
cp .env.example .env.production

# Edit with production settings
ORACLE_PASSWORD=<secure_password>
VITE_API_URL=https://api.jobportal.com
APP_DEBUG=false
```

### Key Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ORACLE_USER` | Database username | `narasimha` |
| `ORACLE_PASSWORD` | Database password | `secure_password` |
| `ORACLE_HOST` | Database host | `oracle-db` |
| `ORACLE_PORT` | Database port | `1521` |
| `ORACLE_SERVICE` | Database service name | `XE` |
| `VITE_API_URL` | Frontend API endpoint | `http://localhost:8000` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |

### Secrets Management

**Using Jenkins Credentials:**
1. Go to Jenkins → Manage Credentials
2. Add new credentials:
   - Type: Username with password
   - ID: `oracle-user-credentials`
   - Username: `narasimha`
   - Password: `<actual_password>`

**Using Docker Secrets (Swarm Mode):**
```bash
echo "narasimha" | docker secret create oracle_user -
echo "password123" | docker secret create oracle_password -
```

## Jenkins Setup

### Jenkins Installation

**Docker Deployment:**
```bash
# Create Jenkins volume for persistence
docker volume create jenkins-data

# Run Jenkins container
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins-data:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts

# Get initial admin password
docker logs jenkins | grep -A 5 "Jenkins initial setup is required"
```

### Initial Configuration

1. **Access Jenkins**
   - Open http://localhost:8080
   - Enter the admin password from the logs
   - Install suggested plugins

2. **Install Required Plugins**
   - Go to Manage Jenkins → Plugin Manager
   - Install:
     - Pipeline
     - Docker Pipeline
     - GitHub Integration
     - Email Extension
     - Slack Notification
     - JUnit Plugin
     - Cobertura Plugin

3. **Create Jenkins Credentials**
   - Username/Password for Docker registry
   - Username/Password for Oracle database
   - Slack webhook URL
   - Email configuration

## Jenkins Pipeline Configuration

### Creating the Pipeline Job

**Step 1: Create a New Job**
```
1. Jenkins Dashboard → New Item
2. Enter job name: "JobPortal-Pipeline"
3. Select "Pipeline"
4. Click OK
```

**Step 2: Configure Pipeline**
```
1. Go to job configuration
2. Pipeline section → Pipeline script from SCM
3. SCM: Git
4. Repository URL: <your-git-repo>
5. Credentials: <select-git-credentials>
6. Script Path: Jenkinsfile
7. Save
```

### Pipeline Parameters

The pipeline accepts the following parameters:

| Parameter | Type | Options | Default |
|-----------|------|---------|---------|
| `DEPLOYMENT_ENVIRONMENT` | Choice | development, staging, production | development |
| `SKIP_TESTS` | Boolean | true/false | false |
| `PUSH_TO_REGISTRY` | Boolean | true/false | false |

### Pipeline Stages

#### 1. Checkout Source Code
- Clones repository
- Logs commit information
- Validates Git history

#### 2. Load Environment
- Loads environment-specific variables
- Falls back to default if not found

#### 3. Validate Project Structure
- Verifies backend directory exists
- Verifies frontend directory exists
- Checks for required files (requirements.txt, package.json, main.py)

#### 4. Install Dependencies
- Backend: Creates virtual environment, installs Python packages
- Frontend: Installs Node.js packages

#### 5. Lint Backend Code
- Runs flake8 linter
- Reports code style issues
- Non-blocking (warnings only)

#### 6. Run Backend Tests
- Executes pytest if tests exist
- Generates coverage reports
- Creates JUnit XML report

#### 7. Run Frontend Build
- Builds React application with Vite
- Optimizes production bundle
- Verifies build output

#### 8. Build Docker Images
- Builds backend image with tags
- Builds frontend image with tags
- Adds metadata (build date, version)

#### 9. Push to Docker Registry (Optional)
- Logs in to Docker registry
- Pushes images with build number tag
- Pushes latest tag

#### 10. Run Docker Compose
- Stops existing containers
- Loads environment configuration
- Starts all services in background

#### 11. Verify Application Health
- Waits for services to be healthy
- Checks backend API endpoint
- Checks frontend service
- Validates database connectivity

#### 12. Run Smoke Tests
- Tests critical API endpoints
- Verifies frontend availability
- Confirms application functionality

#### 13. Generate Reports
- Collects test results
- Aggregates coverage reports
- Creates artifacts

### Post-Build Actions

**Success:**
- Sends Slack notification
- Sends email notification
- Archives reports

**Failure:**
- Sends Slack failure notification
- Sends detailed email with logs
- Attaches console output

**Always:**
- Cleans up temporary files
- Removes build artifacts

## Running the Application

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd final_project

# 2. Create environment file
cp .env.example .env

# 3. Update environment variables
# Edit .env with your Oracle database credentials

# 4. Build and start services
docker-compose up -d

# 5. Verify services are running
docker-compose ps

# 6. Check application
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Manual Testing

```bash
# Test backend API
curl -X GET http://localhost:8000/docs

# Test frontend
curl -X GET http://localhost:3000

# View logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs oracle-db

# Execute database query
docker-compose exec -T oracle-db sqlplus -S sys/narasimha@localhost:1521/XE as sysdba "select 1 from dual;"

# Access backend shell
docker-compose exec backend bash

# Access frontend shell
docker-compose exec frontend sh
```

### Database Initialization

```bash
# View database initialization logs
docker-compose logs oracle-db

# Wait for database to be ready (takes ~2 minutes)
# Check logs for: "DATABASE IS READY TO USE!"

# Connect to database
docker-compose exec -T oracle-db sqlplus -S sys/narasimha@localhost:1521/XE as sysdba

# Run SQL script
docker-compose exec -T oracle-db sqlplus -S sys/narasimha@localhost:1521/XE as sysdba @/path/to/init.sql
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Containers Not Starting

```bash
# Check Docker daemon
docker --version

# View container logs
docker-compose logs

# Check resource usage
docker stats

# Solution: Increase Docker memory allocation
# Docker Desktop Settings → Resources → Memory: 8GB+
```

#### Issue: Database Connection Timeout

```bash
# Verify database container
docker-compose ps oracle-db

# Check database logs
docker-compose logs oracle-db

# Wait longer for database initialization
docker-compose logs --tail=20 oracle-db | grep "DATABASE IS READY"

# Manually verify connection
docker-compose exec -T oracle-db sqlplus -L sys/narasimha@localhost:1521/XE as sysdba
```

#### Issue: Backend Cannot Connect to Database

```bash
# Verify environment variables
docker-compose config | grep ORACLE_

# Check container environment
docker exec <backend-container> env | grep ORACLE

# Test connectivity from backend
docker-compose exec backend curl -v http://oracle-db:1521

# Check network
docker network ls
docker network inspect <network-name>
```

#### Issue: Frontend API Calls Failing

```bash
# Verify API URL
docker-compose exec frontend env | grep VITE_API_URL

# Test from frontend container
docker-compose exec frontend curl http://backend:8000

# Check CORS settings in backend
# Ensure FastAPI CORS middleware is configured correctly

# Verify backend is running
curl -X GET http://localhost:8000/docs
```

#### Issue: Disk Space

```bash
# Clean up Docker resources
docker system prune -a

# Remove volumes (careful - deletes data!)
docker volume prune

# Check disk usage
docker system df
```

#### Issue: Port Already in Use

```bash
# Find process using port
lsof -i :8000    # Backend
lsof -i :3000    # Frontend
lsof -i :1521    # Database

# Kill process (if safe to do so)
kill -9 <PID>

# Or change port in docker-compose.yml and .env
```

### Debugging Commands

```bash
# Comprehensive health check
docker-compose ps
docker-compose exec backend curl http://localhost:8000/docs
docker-compose exec frontend wget -O- http://localhost:3000

# View all logs with timestamps
docker-compose logs --timestamps

# Follow specific service logs
docker-compose logs -f backend --tail=50

# Inspect image layers
docker image history job-portal-backend:latest

# Check image security
docker scout cves job-portal-backend:latest
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Environment variables set correctly
- [ ] Database credentials secured
- [ ] SSL/TLS certificates obtained
- [ ] Docker images tested locally
- [ ] Health checks verified
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Logging aggregation setup

### Production docker-compose.yml Modifications

```yaml
# Use specific image tags instead of latest
services:
  backend:
    image: docker.io/myusername/job-portal-backend:1.0.0-abc123
  frontend:
    image: docker.io/myusername/job-portal-frontend:1.0.0-abc123

# Add restart policies
restart_policy:
  condition: on-failure
  delay: 5s
  max_attempts: 5

# Add resource limits
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 1G
```

### Production Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Create production environment
cp .env.example .env.production
# Edit with production secrets

# 3. Build images
docker-compose build --no-cache

# 4. Stop current services
docker-compose down

# 5. Start new services
docker-compose --env-file .env.production up -d

# 6. Verify health
docker-compose ps
curl https://api.jobportal.com/docs

# 7. Check logs for errors
docker-compose logs --since 5m
```

### Monitoring and Maintenance

```bash
# Monitor resource usage
docker stats --no-stream

# Regular backups
docker-compose exec -T oracle-db expdp sys/narasimha FULL=Y DUMPFILE=backup.dmp

# Update images
docker-compose pull
docker-compose up -d

# View version information
docker image inspect job-portal-backend:latest | grep -i version
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Oracle Database Docker Images](https://github.com/oracle/docker-images)

## Support

For issues and questions:
1. Check the Troubleshooting section above
2. Review Jenkins build logs
3. Check Docker container logs
4. Consult project documentation
5. Contact DevOps team

---

**Last Updated**: 2024
**Version**: 1.0.0
