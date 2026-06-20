# Jenkins CI/CD Pipeline - Complete Implementation Guide

## 📌 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Jenkins Installation](#jenkins-installation)
3. [Jenkins Configuration](#jenkins-configuration)
4. [Pipeline Overview](#pipeline-overview)
5. [Stage-by-Stage Breakdown](#stage-by-stage-breakdown)
6. [Running the Pipeline](#running-the-pipeline)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software & Tools
- ✅ Docker & Docker Compose (for containerized services)
- ✅ Jenkins (2.350+)
- ✅ Git (for source code management)
- ✅ Python 3.11+ (backend development)
- ✅ Node.js 20+ (frontend development)

### System Requirements
- **RAM**: Minimum 8GB (Jenkins + Docker containers)
- **Disk Space**: 20GB free space
- **Network**: Access to Docker registry (if pushing images)

### Jenkins Plugins Required
```
Pipeline
Docker Pipeline
Git
Email Extension
Slack Notification
Cobertura Plugin (for code coverage)
JUnit Plugin (for test results)
Blue Ocean (optional - better UI)
```

---

## Jenkins Installation

### Step 1: Install Jenkins via Docker (Recommended)

```bash
# Create Jenkins home directory
mkdir -p ~/jenkins_home
chmod 777 ~/jenkins_home

# Run Jenkins in Docker
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v ~/jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -u root \
  jenkins/jenkins:latest
```

### Step 2: Get Initial Jenkins Password

```bash
# Retrieve the initial admin password
docker logs jenkins | grep "Please use the following password"

# Or directly read from file
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Step 3: Access Jenkins UI

1. Open browser: `http://localhost:8080`
2. Enter the initial password from Step 2
3. Select **"Install suggested plugins"**
4. Create an admin user account
5. Save and continue

### Step 4: Install Additional Plugins

1. Go to **Manage Jenkins** → **Manage Plugins**
2. Search and install:
   - Docker Pipeline
   - Email Extension
   - Slack Notification
   - Cobertura Plugin
   - JUnit Plugin
   - Blue Ocean (optional)

---

## Jenkins Configuration

### Step 1: Configure System Credentials

#### Add Docker Registry Credentials

1. Go to **Manage Jenkins** → **Manage Credentials**
2. Click **Global** → **Add Credentials**
3. Select **Username with password**
4. Enter:
   - **Username**: Your Docker Hub username
   - **Password**: Your Docker Hub token
   - **ID**: `docker-registry-credentials`
5. Click **Create**

#### Add Oracle Database Credentials

1. Repeat above process
2. Create two credentials:

**Credential 1:**
- **Username**: `narasimha`
- **Password**: Your Oracle password
- **ID**: `oracle-user`

**Credential 2:**
- **Username**: `narasimha`
- **Password**: Your Oracle password
- **ID**: `oracle-password`

#### Add Slack Webhook (Optional)

1. Go to **Manage Jenkins** → **Manage Credentials**
2. Add **Secret text**
3. Paste your Slack webhook URL
4. **ID**: `slack-webhook-url`

#### Add Email Credentials (Optional)

1. Go to **Manage Jenkins** → **System Configuration**
2. Scroll to **Extended E-mail Notification**
3. Configure SMTP server settings

### Step 2: Configure Git Integration

1. Go to **Manage Jenkins** → **Configure System**
2. Scroll to **Git**
3. Set Git executable path: `/usr/bin/git`
4. Click **Save**

### Step 3: Configure Pipeline Default Settings

1. Go to **Manage Jenkins** → **Configure System**
2. Scroll to **Pipeline**
3. Set:
   - **Pipeline speed/durability setting**: `Performance optimized`
4. Click **Save**

---

## Pipeline Overview

Your Jenkinsfile implements a **Declarative Pipeline** with the following flow:

```
┌─────────────────────────────────────────┐
│        PIPELINE STAGES FLOW             │
├─────────────────────────────────────────┤
│ 1. Checkout Source Code                 │
│    ↓                                     │
│ 2. Load Environment                     │
│    ↓                                     │
│ 3. Validate Project Structure           │
│    ↓                                     │
│ 4. Install Backend Dependencies         │
│    ↓                                     │
│ 5. Install Frontend Dependencies        │
│    ↓                                     │
│ 6. Lint Backend Code                    │
│    ↓                                     │
│ 7. Run Backend Tests                    │
│    ↓                                     │
│ 8. Run Frontend Build                   │
│    ↓                                     │
│ 9. Build Docker Images                  │
│    ↓                                     │
│ 10. Push to Docker Registry (optional)  │
│    ↓                                     │
│ 11. Run Docker Compose                  │
│    ↓                                     │
│ 12. Verify Application Health           │
│    ↓                                     │
│ 13. Run Smoke Tests                     │
│    ↓                                     │
│ 14. Generate Reports                    │
│    ↓                                     │
│ SUCCESS / FAILURE / UNSTABLE            │
└─────────────────────────────────────────┘
```

---

## Stage-by-Stage Breakdown

### Stage 1: Checkout Source Code
**Purpose**: Fetch the latest code from Git repository

```groovy
stage('Checkout Source Code') {
    steps {
        checkout scm  // Checks out from Git repository
        // Logs Git info: branch, commit, author
    }
}
```

**What happens**:
- Clones the repository
- Checks out the specified branch/commit
- Displays Git metadata

---

### Stage 2: Load Environment
**Purpose**: Load environment-specific configurations

```groovy
stage('Load Environment') {
    steps {
        // Sources .env.{DEPLOYMENT_ENVIRONMENT} file
        // Sets environment variables for the build
    }
}
```

**What happens**:
- Loads `.env.development`, `.env.staging`, or `.env.production`
- Sets database connection strings, API URLs, etc.

**Files needed**:
```
.env.development
.env.staging
.env.production
```

---

### Stage 3: Validate Project Structure
**Purpose**: Ensure all required directories and files exist

**Validates**:
- ✅ Backend directory exists
- ✅ Frontend directory exists
- ✅ `requirements.txt` (backend dependencies)
- ✅ `main.py` (backend entry point)
- ✅ `package.json` (frontend config)

---

### Stage 4 & 5: Install Dependencies

#### Backend Dependencies
```bash
cd backend_fastapi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Frontend Dependencies
```bash
cd goskill-frontend
npm ci --prefer-offline --no-audit
```

---

### Stage 6: Lint Backend Code
**Purpose**: Check code quality using flake8

```bash
flake8 . --max-line-length=120 --ignore=E501,W503 --exclude=venv
```

**What it checks**:
- PEP 8 compliance
- Unused imports
- Code style issues

---

### Stage 7: Run Backend Tests
**Purpose**: Execute pytest test suite

```bash
pytest --cov=. --cov-report=xml --cov-report=html --junitxml=test-results.xml
```

**Generates**:
- Code coverage reports
- JUnit XML test results
- HTML coverage report

---

### Stage 8: Run Frontend Build
**Purpose**: Build optimized frontend production bundle

```bash
npm run build
```

**Output**:
- `/dist` folder with optimized static files
- Minified JavaScript/CSS
- Asset optimization

---

### Stage 9: Build Docker Images
**Purpose**: Create Docker images for both backend and frontend

```bash
docker build --tag ${DOCKER_IMAGE_BACKEND}:${DOCKER_IMAGE_TAG} backend_fastapi
docker build --tag ${DOCKER_IMAGE_FRONTEND}:${DOCKER_IMAGE_TAG} goskill-frontend
```

**Tags created**:
- `backend:build-number-git-hash`
- `backend:latest`
- `frontend:build-number-git-hash`
- `frontend:latest`

---

### Stage 10: Push to Docker Registry
**Purpose**: Push Docker images to registry (if `PUSH_TO_REGISTRY=true`)

**Pushed to**:
- Docker Hub (or custom registry)
- Tags: `latest` and versioned tags

---

### Stage 11: Run Docker Compose
**Purpose**: Start all services (backend, frontend, database)

```bash
docker-compose --env-file .env.${DEPLOYMENT_ENVIRONMENT} up -d
```

**Services started**:
- 🐋 FastAPI Backend (port 8000)
- 🌐 React Frontend (port 3000)
- 🗄️ Oracle Database (port 1521)

---

### Stage 12: Verify Application Health
**Purpose**: Health checks to ensure services are running

**Checks**:
```
✓ Backend API /docs endpoint (30 retries, 2s intervals)
✓ Frontend service (30 retries, 2s intervals)
⚠️ Oracle database (if sqlplus available)
```

---

### Stage 13: Run Smoke Tests
**Purpose**: Quick validation that main endpoints work

```bash
curl -f http://localhost:8000/docs  # API docs
curl -f http://localhost:3000       # Frontend
```

---

### Stage 14: Generate Reports
**Purpose**: Collect test artifacts and coverage reports

**Collected**:
- `test-results.xml` (JUnit format)
- `htmlcov/` (HTML coverage report)

---

## Running the Pipeline

### Method 1: Create New Job in Jenkins UI

1. Click **New Item** on Jenkins home
2. Enter job name: `job-portal-pipeline`
3. Select **Pipeline**
4. Click **OK**
5. In **Pipeline** section:
   - Select **Pipeline script from SCM**
   - **SCM**: Git
   - **Repository URL**: Your Git repo URL
   - **Branch**: `*/main` or `*/develop`
   - **Script Path**: `Jenkinsfile`
6. Click **Save**

### Method 2: Run via CLI

```bash
# Trigger Jenkins job
curl -X POST http://localhost:8080/job/job-portal-pipeline/build \
  -u admin:admin_password \
  -F token=YOUR_TOKEN
```

### Method 3: Run with Build Parameters

1. Click **Build with Parameters** (after first run)
2. Select:
   - **DEPLOYMENT_ENVIRONMENT**: `development` / `staging` / `production`
   - **SKIP_TESTS**: `false` / `true`
   - **PUSH_TO_REGISTRY**: `false` / `true`
3. Click **Build**

---

## Environment Variables

### Pipeline Parameters (User Selection)
| Parameter | Options | Default |
|-----------|---------|---------|
| `DEPLOYMENT_ENVIRONMENT` | development, staging, production | development |
| `SKIP_TESTS` | true, false | false |
| `PUSH_TO_REGISTRY` | true, false | false |

### Environment Variables (Auto-set)
| Variable | Value |
|----------|-------|
| `PROJECT_NAME` | JobPortal |
| `PROJECT_VERSION` | 1.0.0 |
| `DOCKER_IMAGE_TAG` | `${BUILD_NUMBER}-${GIT_COMMIT.take(7)}` |
| `NODE_ENV` | production |
| `PYTHONUNBUFFERED` | 1 |

### Credentials (From Jenkins)
| Credential | Used For |
|-----------|----------|
| `oracle-user` | Database authentication |
| `oracle-password` | Database authentication |
| `docker-registry-credentials` | Docker image push |
| `slack-webhook-url` | Slack notifications |

---

## Notifications

### Slack Notifications
- ✅ **Success**: Green message with build details
- ❌ **Failure**: Red message with failure info
- ⚠️ **Unstable**: Yellow message with warning

### Email Notifications
- **On Success**: Confirmation email with build info
- **On Failure**: Error email with console output attached

---

## Troubleshooting

### Issue 1: Build Times Out
**Problem**: Build exceeds 1 hour

**Solution**:
1. Modify `timeout(time: 1, unit: 'HOURS')` in Jenkinsfile
2. Set to `timeout(time: 2, unit: 'HOURS')`

### Issue 2: Docker Images Not Building
**Problem**: Docker build command fails

**Solutions**:
```bash
# Check Docker daemon is running
docker ps

# Check Dockerfile exists
ls backend_fastapi/Dockerfile
ls goskill-frontend/Dockerfile

# Test manual build
docker build -t test backend_fastapi
```

### Issue 3: Oracle Database Connection Failed
**Problem**: Database health check fails

**Solutions**:
```bash
# Check Oracle container is running
docker ps | grep oracle

# Check connection string
docker exec oracle-db sqlplus -v

# Verify credentials in Jenkins
```

### Issue 4: Tests Failing Locally but Passing in CI
**Problem**: Environment-specific test failures

**Solutions**:
1. Set same environment variables locally
2. Use same database version
3. Check file paths (relative vs absolute)

### Issue 5: Docker Registry Push Fails
**Problem**: Authentication error when pushing images

**Solutions**:
```bash
# Verify Docker credentials in Jenkins
# Check registry access
docker login docker.io

# Verify image tag format
docker images | grep job-portal
```

---

## Best Practices

### 1. Pipeline Configuration
- ✅ Use descriptive stage names
- ✅ Add logging/echoing for debugging
- ✅ Set timeouts for long-running stages
- ✅ Use credentials from Jenkins vault, not hardcoded

### 2. Testing
- ✅ Write unit tests (pytest for Python)
- ✅ Write integration tests
- ✅ Run tests before building Docker images
- ✅ Generate code coverage reports

### 3. Docker Images
- ✅ Use multi-stage builds (smaller images)
- ✅ Tag images with version and commit hash
- ✅ Use non-root user in containers
- ✅ Include health checks

### 4. Deployment
- ✅ Use environment-specific configs
- ✅ Run smoke tests after deployment
- ✅ Keep deployment logs
- ✅ Use health checks to verify services

### 5. Monitoring
- ✅ Set up Slack notifications
- ✅ Send email alerts on failures
- ✅ Monitor build times
- ✅ Archive artifacts for debugging

---

## Quick Reference Commands

### Jenkins CLI
```bash
# Check Jenkins status
docker exec jenkins curl http://localhost:8080

# View Jenkins logs
docker logs jenkins

# Enter Jenkins container
docker exec -it jenkins bash

# Restart Jenkins
docker restart jenkins
```

### Docker Compose (From Pipeline)
```bash
# View running services
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v
```

### Git Commands
```bash
# Check current branch
git rev-parse --abbrev-ref HEAD

# Get commit hash
git rev-parse HEAD

# Get commit author
git log -1 --format=%an
```

---

## Next Steps

1. **Setup Jenkins**: Install and configure as per Section 2-3
2. **Add Credentials**: Add Docker, Oracle, Slack credentials
3. **Create Pipeline Job**: Create job with Jenkinsfile from SCM
4. **Test Pipeline**: Run initial build to verify all stages work
5. **Configure Notifications**: Setup Slack and email alerts
6. **Monitor Builds**: Use Blue Ocean for better visualization

---

## Additional Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Declarative Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Docker & Jenkins Integration](https://plugins.jenkins.io/docker-workflow/)
- [Pipeline Best Practices](https://www.jenkins.io/doc/book/pipeline/pipeline-best-practices/)

