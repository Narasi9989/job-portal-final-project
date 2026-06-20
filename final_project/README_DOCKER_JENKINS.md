# Job Portal - Docker & Jenkins CI/CD Implementation Guide

## 📋 Overview

This comprehensive implementation provides:

✅ **Complete Docker Containerization**
- Multi-stage builds for optimization
- FastAPI backend container
- React/Vite frontend container
- Oracle database container orchestration

✅ **Production-Ready Jenkins CI/CD Pipeline**
- Automated testing and building
- Docker image creation and registry push
- Health checks and smoke tests
- Deployment notifications

✅ **Environment Management**
- Development, staging, and production configurations
- Secrets management with environment variables
- Security best practices

✅ **Comprehensive Documentation**
- Docker setup and commands
- Jenkins configuration guide
- Troubleshooting guide
- Command reference

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Verify installations
docker --version        # Docker 20.10+
docker-compose --version # Docker Compose 2.0+
git --version           # Git 2.30+
```

### 2. Initial Setup (5 minutes)
```bash
# Clone/Navigate to project
cd final_project

# Setup environment
cp .env.example .env.development

# Start all services
docker-compose up -d

# Verify services
docker-compose ps
```

### 3. Access the Application
```
Backend API: http://localhost:8000/docs
Frontend: http://localhost:3000
Database: localhost:1521 (Oracle XE)
```

### 4. Stop Services
```bash
docker-compose down
```

---

## 📁 Files Generated

### Docker Files
| File | Purpose |
|------|---------|
| `backend_fastapi/Dockerfile` | Multi-stage FastAPI container |
| `goskill-frontend/Dockerfile` | Multi-stage React container |
| `docker-compose.yml` | Orchestrates all services |
| `backend_fastapi/.dockerignore` | Excludes unnecessary files |
| `goskill-frontend/.dockerignore` | Excludes unnecessary files |

### Configuration Files
| File | Purpose |
|------|---------|
| `.env.example` | Template for all environments |
| `.env.development` | Development settings |
| `.env.staging` | Staging/pre-prod settings |
| `.env.production` | Production settings |

### CI/CD Files
| File | Purpose |
|------|---------|
| `Jenkinsfile` | Jenkins pipeline definition |
| `jenkins-setup.sh` | Automated Jenkins setup |
| `deploy-production.sh` | Production deployment script |

### Documentation
| File | Purpose |
|------|---------|
| `DOCKER_JENKINS_SETUP.md` | Detailed setup guide (100+ pages) |
| `COMMANDS_REFERENCE.md` | Quick command reference |
| `Makefile` | Common command shortcuts |

---

## 🐳 Docker Quick Commands

### Using Makefile (Recommended)
```bash
# View all commands
make help

# Basic operations
make up              # Start services
make down            # Stop services
make logs           # View all logs
make health         # Check health
make rebuild        # Clean and rebuild

# Testing
make test           # Run tests
make lint-backend   # Lint backend code

# Advanced
make push           # Push to registry
make jenkins-setup  # Setup Jenkins
```

### Direct Docker Compose
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Clean everything
docker-compose down -v
```

---

## 🔄 Jenkins CI/CD Pipeline

### Pipeline Stages

1. **Checkout Source Code** - Pulls latest from Git
2. **Load Environment** - Loads environment-specific variables
3. **Validate Project Structure** - Verifies project integrity
4. **Install Dependencies** - Installs backend and frontend dependencies
5. **Lint Backend Code** - Checks code style with flake8
6. **Run Backend Tests** - Executes pytest with coverage
7. **Run Frontend Build** - Builds optimized React bundle
8. **Build Docker Images** - Creates Docker images
9. **Push to Docker Registry** - Optional: Pushes to registry
10. **Run Docker Compose** - Starts all services
11. **Verify Application Health** - Checks service health
12. **Run Smoke Tests** - Tests critical functionality

### Setup Jenkins

```bash
# 1. Using provided script
bash jenkins-setup.sh

# 2. Manual setup
# - Go to http://localhost:8080
# - Install Pipeline plugin
# - Create new Pipeline job
# - Point to Jenkinsfile in repository
# - Add credentials (Docker, Oracle, Slack)
# - Run build
```

### Parameters

When triggering a build, you can specify:
- `DEPLOYMENT_ENVIRONMENT`: development, staging, production
- `SKIP_TESTS`: true/false
- `PUSH_TO_REGISTRY`: true/false

---

## 🔐 Environment Configuration

### Development (.env.development)
```
ORACLE_USER=narasimha
ORACLE_PASSWORD=narasimha
ORACLE_HOST=oracle-db
VITE_API_URL=http://localhost:8000
APP_DEBUG=true
```

### Production (.env.production)
```
ORACLE_USER=prod_user
ORACLE_PASSWORD=<from vault>
ORACLE_HOST=oracle-db.prod.internal
VITE_API_URL=https://api.jobportal.com
APP_DEBUG=false
```

### Secrets Management
```bash
# Use Jenkins Credentials
# Manage Jenkins → Manage Credentials → Add Credentials

# Required credentials:
- oracle-user (Username/Password)
- docker-registry-credentials (Username/Password)
- slack-webhook-url (Secret text)
- github-token (Secret text)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Jenkins CI/CD Pipeline            │
└────────────┬────────────────────────┘
             │
    ┌────────▼─────────────┐
    │  Docker Compose      │
    │  Orchestration       │
    └┬───────┬──────────┬──┘
     │       │          │
  ┌──▼──┐ ┌─▼──┐   ┌───▼───┐
  │Fast │ │React │   │ Oracle│
  │API  │ │App  │   │ DB    │
  └─────┘ └─────┘   └───────┘
     8000   3000      1521
```

### Container Network
- **Network**: job-portal-network (bridge)
- **Backend → Database**: oracle-db:1521
- **Frontend → Backend**: backend:8000
- **External**: All ports exposed

---

## 📊 Key Features

### Dockerfile Features
✅ Multi-stage builds for size optimization
✅ Non-root user execution (recommended)
✅ Health checks included
✅ Minimal production images
✅ Build metadata (version, date, commit)

### Docker Compose Features
✅ Service dependencies configured
✅ Health checks with retries
✅ Persistent volumes for data
✅ Environment variable management
✅ Automatic service restart

### Jenkins Pipeline Features
✅ Parameterized builds
✅ Environment-specific deployments
✅ Comprehensive logging
✅ Email and Slack notifications
✅ Automatic cleanup
✅ Smoke testing
✅ Post-build actions

---

## 🔍 Monitoring and Troubleshooting

### Check Service Health
```bash
# Using make
make health

# Using docker-compose
docker-compose ps
docker-compose logs backend
docker-compose logs frontend
docker-compose logs oracle-db

# Using curl
curl http://localhost:8000/docs
curl http://localhost:3000
```

### Common Issues

**Issue**: Backend cannot connect to database
```bash
# Solution
docker-compose logs oracle-db
# Wait ~2 minutes for database initialization
# Check ORACLE_HOST=oracle-db in docker-compose.yml
```

**Issue**: Port already in use
```bash
# Solution
# Change port in .env or docker-compose.yml
# Or stop conflicting container:
docker stop <container>
```

**Issue**: Frontend API calls failing
```bash
# Solution
# Verify VITE_API_URL is set correctly
docker-compose exec frontend env | grep VITE_API_URL
# Check CORS in backend FastAPI configuration
```

**Full troubleshooting guide**: See `DOCKER_JENKINS_SETUP.md`

---

## 📦 Deployment

### Development
```bash
docker-compose --env-file .env.development up -d
```

### Staging
```bash
docker-compose --env-file .env.staging up -d
```

### Production
```bash
# Automated deployment with backup and rollback
bash deploy-production.sh

# Rollback if needed
bash deploy-production.sh rollback
```

---

## 📖 Documentation Structure

1. **DOCKER_JENKINS_SETUP.md** (100+ pages)
   - Complete setup guide
   - Docker best practices
   - Jenkins configuration
   - Production deployment
   - Troubleshooting guide

2. **COMMANDS_REFERENCE.md**
   - Quick reference for all commands
   - Docker Compose operations
   - Jenkins CLI operations
   - Networking and connectivity
   - Health checks and monitoring

3. **This README**
   - Quick start
   - Architecture overview
   - Common commands
   - Key features

---

## 🚦 Project Status Check

Use Makefile to verify everything:

```bash
# Comprehensive validation
make verify

# Expected output:
# ✓ Backend main.py found
# ✓ Backend requirements.txt found
# ✓ Frontend package.json found
# ✓ docker-compose.yml found
# ✓ Jenkinsfile found
# ✓ .env.example found
```

---

## 📋 Pre-Deployment Checklist

Before deploying to production:

- [ ] All environment variables set correctly
- [ ] Database credentials are secure
- [ ] SSL/TLS certificates obtained
- [ ] Docker images tested locally
- [ ] Health checks verified
- [ ] Backup strategy implemented
- [ ] Monitoring and logging configured
- [ ] Rollback procedure documented
- [ ] Team trained on deployment process
- [ ] Documentation updated

---

## 🔐 Security Notes

### Development
✅ Simple credentials (fine for local development)
✅ APP_DEBUG=true for detailed error messages
✅ HTTP connections allowed

### Production
⚠️ **NEVER commit .env.production**
⚠️ Use vault/secrets manager for credentials
⚠️ APP_DEBUG=false in production
⚠️ Use HTTPS/TLS for all connections
⚠️ Regular security updates
⚠️ Monitor for vulnerabilities

```bash
# Scan Docker images for vulnerabilities
docker scout cves job-portal-backend:latest
docker scout cves job-portal-frontend:latest
```

---

## 🛠️ Maintenance

### Regular Tasks
```bash
# Update dependencies
docker-compose pull

# Backup database
docker-compose exec -T oracle-db expdp sys/password FULL=Y DUMPFILE=backup.dmp

# Monitor resources
docker stats

# Clean up unused resources
docker system prune -a
```

### Version Updates
```bash
# Update Docker images
docker pull python:3.11-slim
docker pull node:20-alpine
docker pull container-registry.oracle.com/database/enterprise:latest

# Rebuild with new base images
docker-compose build --no-cache
```

---

## 📞 Support and Troubleshooting

### Getting Help
1. Check `DOCKER_JENKINS_SETUP.md` → Troubleshooting section
2. Review `COMMANDS_REFERENCE.md` for command examples
3. Check Jenkins build logs
4. Review Docker container logs
5. Consult project documentation

### Useful Logs
```bash
# Backend application logs
docker-compose logs backend

# Database logs
docker-compose logs oracle-db

# Frontend build logs
docker-compose logs frontend

# Jenkins logs
docker logs jenkins
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Oracle Docker Images](https://github.com/oracle/docker-images)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial release - Complete Docker & Jenkins implementation |

---

## 📞 Contact

For issues, questions, or improvements:
1. Check existing documentation
2. Review troubleshooting guide
3. Check Jenkins build logs
4. Contact DevOps team

---

**Happy deploying! 🚀**

For detailed information on any topic, refer to:
- **Docker/Compose Setup**: `DOCKER_JENKINS_SETUP.md`
- **Command Reference**: `COMMANDS_REFERENCE.md`
- **Quick Commands**: Use `make help`
