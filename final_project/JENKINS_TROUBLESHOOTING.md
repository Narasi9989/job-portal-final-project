# Jenkins Jenkinsfile Troubleshooting Guide

## ✅ Fixes Applied

Your Jenkinsfile has been corrected with the following improvements:

### 1. ✅ Simplified Environment Variables
- Removed complex credential references that were causing failures
- Now uses simple credentials: `docker-username`, `docker-password`
- Slack webhook is optional (won't fail if not configured)

### 2. ✅ Fixed Virtual Environment Activation
- Changed from unreliable `. venv/bin/activate || source venv/Scripts/activate`
- To proper conditional check:
```bash
if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
else
    source venv/Scripts/activate 2>/dev/null || . venv/Scripts/activate
fi
```

### 3. ✅ Made Notifications Optional
- Slack notifications now check if webhook exists before sending
- Email notifications wrapped in try-catch blocks
- Pipeline won't fail if notifications aren't configured

### 4. ✅ Fixed Docker Registry Login
- Simplified to use direct credentials without registry URL
- Works with Docker Hub (docker.io)

### 5. ✅ Removed Unused Code
- Removed helper functions that weren't being used
- Cleaned up unnecessary complexity

---

## 🔧 Pre-Requisites: What You Must Configure in Jenkins

Before running the pipeline, configure these credentials in Jenkins:

### Step 1: Add Docker Credentials

1. Go to **Jenkins Dashboard** → **Manage Jenkins** → **Manage Credentials**
2. Click **Global** under Stores
3. Click **Add Credentials** → **Jenkins**
4. Fill in:
   - **Kind**: Username with password
   - **Scope**: Global
   - **Username**: `your-docker-username` (e.g., `john_doe`)
   - **Password**: `your-docker-password` (or Docker Hub token)
   - **ID**: `docker-username`
   - **Description**: Docker Registry Username
5. Click **Create**

6. **Repeat** to create second credential:
   - **Kind**: Secret text
   - **Scope**: Global
   - **Secret**: `your-docker-password` (or Docker Hub token)
   - **ID**: `docker-password`
   - **Description**: Docker Registry Password
7. Click **Create**

### Step 2: Create Jenkins Job

1. Click **+ New Item** on Jenkins Dashboard
2. Enter Job name: `Job-Portal-Pipeline`
3. Select **Pipeline**
4. Click **OK**
5. Scroll to **Pipeline** section
6. In **Definition**, select **Pipeline script from SCM**
7. **SCM**: Git
8. **Repository URL**: `https://github.com/YOUR_USERNAME/final_project.git`
9. **Branch**: `*/main` (or your branch)
10. **Script Path**: `final_project/Jenkinsfile`
11. Click **Save**

### Step 3: Test the Pipeline

1. Click **Build with Parameters** (if parameters already set up)
2. Or just click **Build Now**
3. Select parameters:
   - **DEPLOYMENT_ENVIRONMENT**: `development`
   - **SKIP_TESTS**: `false`
   - **PUSH_TO_REGISTRY**: `false` (for first run)
4. Click **Build**

---

## ⚠️ Common Errors & Solutions

### Error 1: "Credentials 'docker-username' could not be found"

**Cause**: Credentials not configured in Jenkins

**Solution**:
```bash
# Step 1: Go to Jenkins → Manage Credentials
# Step 2: Create credentials with exact ID: docker-username
# Step 3: Create credentials with exact ID: docker-password
```

**Verification**:
- Go to Manage Credentials
- Search for `docker-username` 
- Should appear in list

---

### Error 2: "venv/bin/activate: No such file or directory"

**Cause**: Virtual environment doesn't exist or path is wrong

**Solution**:
```bash
# The Jenkinsfile now creates it automatically:
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
```

**If still failing**:
1. Check Python 3 is installed: `python3 --version`
2. Check pip works: `python3 -m pip --version`
3. Try manual setup:
```bash
cd backend_fastapi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Error 3: "No such file or directory: backend_fastapi/requirements.txt"

**Cause**: Backend directory not found in the workspace

**Solution**:
1. Verify repository structure:
```bash
ls -la
# Should see:
# backend_fastapi/
# goskill-frontend/
# Jenkinsfile
```

2. If paths are different, update Jenkinsfile:
```groovy
// Change these lines:
BACKEND_PATH = 'your-actual-backend-path'
FRONTEND_PATH = 'your-actual-frontend-path'
```

---

### Error 4: "docker: command not found"

**Cause**: Docker is not installed or not in PATH

**Solution**:
```bash
# Install Docker
# Windows: Download Docker Desktop from docker.com
# Linux: curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh

# Verify installation
docker --version
docker ps

# If using Jenkins in container, ensure Docker socket is mounted:
docker run -d \
  --name jenkins \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:latest
```

---

### Error 5: "npm: command not found"

**Cause**: Node.js/npm not installed on Jenkins agent

**Solution**:
```bash
# Install Node.js
# Windows: Download from nodejs.org
# Linux (Ubuntu):
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version
npm --version
```

---

### Error 6: "Build failed: Backend health check failed"

**Cause**: Backend service didn't start or API isn't responding

**Solution**:
1. Check if backend Dockerfile exists: `ls backend_fastapi/Dockerfile`
2. Test manual Docker build:
```bash
cd backend_fastapi
docker build -t test-backend:latest .
docker run -d -p 8000:8000 test-backend:latest
sleep 5
curl http://localhost:8000/docs
```

3. If manual run works but pipeline fails, check logs:
```bash
docker logs <container-id>
```

---

### Error 7: "Database connection failed"

**Cause**: Oracle database not running or credentials wrong

**Solution**: Skip database checks for development:
```groovy
// In Jenkinsfile, comment out the database health check:
// if docker-compose exec -T oracle-db sqlplus ... then
```

Or ensure Oracle is running:
```bash
docker-compose ps
# Should show oracle-db container running
```

---

### Error 8: "Slack notification failed"

**Cause**: Slack webhook not configured (this should NOT fail the build)

**Solution**: 
- If Slack notifications are important:
  1. Go to Jenkins → Manage Credentials
  2. Create new Secret text credential
  3. Paste your Slack webhook URL
  4. ID: `slack-webhook-url`
  5. Click Create

- If you don't need Slack, it's fine - the pipeline is now tolerant of missing webhooks

---

### Error 9: "Email notification failed"

**Cause**: Email not configured in Jenkins

**Solution** (Optional - Build won't fail):
1. Go to Jenkins → Configure System
2. Scroll to **Extended E-mail Notification**
3. Set SMTP server details
4. Click Save

Or ignore - the pipeline now wraps email in try-catch

---

### Error 10: "Frontend build failed: npm run build"

**Cause**: Build script not found or dependencies not installed

**Solution**:
1. Verify build script in package.json:
```bash
cd goskill-frontend
grep '"build"' package.json
# Should show: "build": "vite build" or similar
```

2. Check for build errors:
```bash
npm install
npm run build
# Look for actual error messages
```

3. Common issues:
   - Missing node_modules: `npm install --legacy-peer-deps`
   - TypeScript errors: Fix in source code
   - Environment variables: Set `VITE_API_URL`

---

## 🧪 Testing the Pipeline Locally

Before running on Jenkins, test locally:

### Test 1: Validate Jenkinsfile Syntax

```bash
# Install Jenkins CLI (if available)
jenkins-cli validate-file Jenkinsfile

# Or use online validator
# https://www.jenkins.io/doc/book/pipeline/syntax/
```

### Test 2: Test Individual Stages Manually

```bash
# Stage 1: Validate structure
ls backend_fastapi/requirements.txt
ls goskill-frontend/package.json

# Stage 2: Install backend dependencies
cd backend_fastapi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Stage 3: Install frontend dependencies
cd ../goskill-frontend
npm install

# Stage 4: Build frontend
npm run build

# Stage 5: Build Docker images
docker build -t job-portal-backend:latest ../backend_fastapi
docker build -t job-portal-frontend:latest .
```

### Test 3: Test Docker Compose

```bash
# From root directory
docker-compose up -d
docker-compose ps
# Should see 3 containers running

# Test endpoints
curl http://localhost:8000/docs  # Backend
curl http://localhost:3000       # Frontend

docker-compose down
```

---

## ✅ Verification Checklist

Before declaring the pipeline working, verify:

- [ ] Docker is installed and running
- [ ] Docker credentials added to Jenkins
- [ ] Pipeline job created with Jenkinsfile
- [ ] Git repository properly configured
- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] Docker Compose installed
- [ ] `.env.development` file exists (or created from `.env.example`)
- [ ] All required directories exist (backend_fastapi, goskill-frontend)

---

## 📊 Pipeline Execution Checklist

When running the pipeline, expected output:

1. ✅ **Checkout** - Git logs appear
2. ✅ **Load Environment** - .env file loaded message
3. ✅ **Validate Structure** - All checks pass
4. ✅ **Install Dependencies** - pip/npm install completes
5. ✅ **Lint** - flake8 output (or skipped if SKIP_TESTS=true)
6. ✅ **Test** - pytest output (or skipped if SKIP_TESTS=true)
7. ✅ **Frontend Build** - "Frontend build completed successfully"
8. ✅ **Docker Build** - "Docker images built successfully"
9. ✅ **Docker Compose** - "Docker Compose started successfully"
10. ✅ **Health Check** - "✓ Backend is healthy", "✓ Frontend is healthy"
11. ✅ **Smoke Tests** - "Smoke tests passed"
12. ✅ **Cleanup** - "Cleanup completed"

---

## 🚀 Quick Start Commands

Run these commands to get everything working:

```bash
# 1. Verify prerequisites
docker --version      # Should be 20.10+
docker-compose --version  # Should be 2.0+
python3 --version     # Should be 3.11+
node --version        # Should be 20+

# 2. Setup environment file
cp final_project/.env.example final_project/.env.development

# 3. Create Jenkins credentials (manual in UI)
# See Step 1 above

# 4. Create Jenkins job (manual in UI)
# See Step 2 above

# 5. Trigger first build
# Via Jenkins UI: Click "Build with Parameters"
# Or via CLI:
curl -X POST http://localhost:8080/job/Job-Portal-Pipeline/build \
  -u admin:YOUR_JENKINS_TOKEN
```

---

## 📞 Still Having Issues?

1. **Check Jenkins Logs**:
```bash
# If Jenkins in Docker
docker logs jenkins

# Or via Jenkins UI:
# Dashboard → Job → Build → Console Output
```

2. **Enable Debug Mode**:
```groovy
// Add this to Jenkinsfile for more verbose output
sh 'set -x' // Before commands you want to debug
```

3. **Check System Requirements**:
- Disk space: `df -h` (need 20GB free)
- RAM: `free -h` (need 8GB+)
- CPU: At least 2 cores

4. **Common Paths**:
- Jenkins home (Docker): `/var/jenkins_home`
- Docker socket: `/var/run/docker.sock`
- Workspace: `/var/jenkins_home/workspace/Job-Portal-Pipeline`

---

## ✨ Success Indicators

Your pipeline is working correctly when:

✅ All 14 stages complete without errors  
✅ Docker images are built and tagged  
✅ Services are running (docker-compose ps shows 3 containers)  
✅ Health checks pass (backend, frontend accessible)  
✅ Build summary shows SUCCESS  
✅ No red X marks in pipeline visualization  

---

**Need more help?** Check the detailed guides:
- [JENKINS_CICD_GUIDE.md](JENKINS_CICD_GUIDE.md) - Complete Jenkins setup
- [DOCKER_JENKINS_SETUP.md](DOCKER_JENKINS_SETUP.md) - Docker configuration
- [README_DOCKER_JENKINS.md](README_DOCKER_JENKINS.md) - Quick reference
