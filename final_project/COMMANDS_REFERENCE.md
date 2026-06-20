# Docker and Jenkins Commands Quick Reference

## Docker Compose Quick Commands

### Starting and Stopping Services

```bash
# Start all services in background
docker-compose up -d

# Start with environment file
docker-compose --env-file .env.production up -d

# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend

# Build without cache
docker-compose build --no-cache

# Build and start
docker-compose up -d --build
```

### Viewing Logs

```bash
# View all logs
docker-compose logs

# Follow logs (real-time)
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f oracle-db

# Last 100 lines
docker-compose logs --tail=100

# View logs with timestamps
docker-compose logs -f --timestamps
```

### Checking Status

```bash
# List all containers
docker-compose ps

# Inspect service
docker-compose exec backend curl http://localhost:8000/docs

# Execute command in container
docker-compose exec backend python -m pip list

# Interactive shell in container
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Database Operations

```bash
# Access database
docker-compose exec -T oracle-db sqlplus -S sys/narasimha@localhost:1521/XE as sysdba

# Run SQL query
docker-compose exec -T oracle-db sqlplus -S sys/narasimha@localhost:1521/XE as sysdba "SELECT * FROM all_users;"

# Backup database
docker-compose exec -T oracle-db expdp sys/narasimha FULL=Y DUMPFILE=backup.dmp

# Restore database
docker-compose exec -T oracle-db impdp sys/narasimha FULL=Y DUMPFILE=backup.dmp
```

### Cleaning Up

```bash
# Remove unused volumes
docker volume prune

# Remove unused images
docker image prune

# Remove all unused resources
docker system prune -a

# Remove specific volume
docker volume rm volume_name
```

## Docker Image Management

### Building Images

```bash
# Build backend image
docker build -t job-portal-backend:latest ./backend_fastapi

# Build frontend image
docker build -t job-portal-frontend:latest ./goskill-frontend

# Build with tags
docker build -t job-portal-backend:1.0.0 ./backend_fastapi
docker build -t registry.example.com/job-portal-backend:latest ./backend_fastapi

# Build with build arguments
docker build \
  --build-arg VERSION=1.0.0 \
  --build-arg BUILD_DATE=$(date) \
  -t job-portal-backend:latest \
  ./backend_fastapi
```

### Running Containers

```bash
# Run container interactively
docker run -it job-portal-backend:latest bash

# Run container in background
docker run -d --name backend -p 8000:8000 job-portal-backend:latest

# Run with environment variables
docker run -d \
  -e ORACLE_USER=narasimha \
  -e ORACLE_PASSWORD=narasimha \
  -p 8000:8000 \
  job-portal-backend:latest

# Run with volume mount
docker run -d \
  -v $(pwd)/uploads:/app/uploads \
  -p 8000:8000 \
  job-portal-backend:latest
```

### Image Management

```bash
# List images
docker images

# Remove image
docker rmi job-portal-backend:latest

# Tag image
docker tag job-portal-backend:latest registry.example.com/job-portal-backend:1.0.0

# Push to registry
docker push registry.example.com/job-portal-backend:1.0.0

# Pull from registry
docker pull registry.example.com/job-portal-backend:latest
```

## Jenkins Pipeline Commands

### Starting Jenkins

```bash
# Run Jenkins with Docker
docker run -d \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins-data:/var/jenkins_home \
  jenkins/jenkins:lts

# Access Jenkins
# http://localhost:8080

# Get admin password
docker logs jenkins | grep "Jenkins initial setup is required"
```

### Jenkins CLI Operations

```bash
# Download Jenkins CLI
wget http://localhost:8080/jnlpJars/jenkins-cli.jar

# Get Jenkins version
java -jar jenkins-cli.jar -s http://localhost:8080 version

# List all jobs
java -jar jenkins-cli.jar -s http://localhost:8080 list-jobs

# Create job from XML
java -jar jenkins-cli.jar -s http://localhost:8080 create-job JobPortal < config.xml

# Delete job
java -jar jenkins-cli.jar -s http://localhost:8080 delete-job JobPortal

# Trigger build
java -jar jenkins-cli.jar -s http://localhost:8080 build JobPortal-Pipeline

# Get job status
java -jar jenkins-cli.jar -s http://localhost:8080 get-job JobPortal-Pipeline

# Get last build status
java -jar jenkins-cli.jar -s http://localhost:8080 get-job JobPortal-Pipeline | grep -i result
```

### Using Makefile

```bash
# Make sure Makefile is in project root

# View all available commands
make help

# Build Docker images
make build

# Start services
make up

# Stop services
make down

# View logs
make logs

# Check health
make health

# Run tests
make test

# Lint code
make lint-backend

# Clean everything
make clean

# Rebuild
make rebuild

# Setup environment
make setup

# Run Jenkins setup
make jenkins-setup
```

## Network and Connectivity

### Docker Networks

```bash
# List networks
docker network ls

# Create network
docker network create job-portal-network

# Inspect network
docker network inspect job-portal-network

# Connect container to network
docker network connect job-portal-network backend-container

# Disconnect container from network
docker network disconnect job-portal-network backend-container
```

### Testing Connectivity

```bash
# Test backend from frontend container
docker-compose exec frontend curl http://backend:8000

# Test database from backend container
docker-compose exec backend curl http://oracle-db:1521

# Test ports are listening
docker-compose exec backend netstat -tuln | grep 8000

# Check container IP
docker inspect -f '{{.NetworkSettings.IPAddress}}' container_name

# DNS resolution test
docker-compose exec backend nslookup oracle-db
```

## Environment and Configuration

### Environment Management

```bash
# Create environment file from example
cp .env.example .env.development

# Use specific environment file
docker-compose --env-file .env.production up -d

# Set environment variables on command line
ORACLE_PASSWORD=secret docker-compose up -d

# Export environment from file
export $(cat .env | grep -v '#' | xargs)
docker-compose up -d
```

### Configuration Validation

```bash
# Validate docker-compose.yml
docker-compose config

# Show resolved environment variables
docker-compose config | grep -A 5 "environment"

# Print specific service config
docker-compose config --services

# Check which environment file is used
docker-compose --env-file .env.production config | grep ORACLE_
```

## Health Checks and Monitoring

### Health Checks

```bash
# Check Docker health
docker-compose exec backend curl http://localhost:8000/health || echo "unhealthy"

# Monitor containers in real-time
docker stats

# View container health status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Inspect health check logs
docker inspect --format='{{json .State.Health}}' container_name | python -m json.tool
```

### Resource Monitoring

```bash
# View resource usage
docker stats --no-stream

# Get container memory usage
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

# Show disk space used by Docker
docker system df

# Show disk space per image
docker images --format "table {{.Repository}}\t{{.Size}}"
```

## Troubleshooting Commands

### Debug and Troubleshoot

```bash
# View detailed container info
docker inspect container_name

# Check container logs
docker logs container_name

# Follow logs with tail
docker logs -f --tail=50 container_name

# Copy files from container
docker cp container_name:/path/to/file ./local/path

# Copy files to container
docker cp ./local/file container_name:/path/to/file

# Commit changes to image
docker commit container_name myimage:latest

# Inspect image layers
docker history job-portal-backend:latest

# Check image security
docker scout cves job-portal-backend:latest
```

### Port Management

```bash
# Find what's using a port
lsof -i :8000    # On Linux/Mac

# Kill process on port (Linux/Mac)
kill -9 $(lsof -t -i :8000)

# Change port mapping (edit docker-compose.yml)
# ports:
#   - "8001:8000"  # Maps host port 8001 to container port 8000
```

## Performance and Optimization

### Image Optimization

```bash
# Check image layers
docker history job-portal-backend:latest

# Inspect image size
docker images --format "table {{.Repository}}\t{{.Size}}" | grep job-portal

# Remove dangling images
docker image prune

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t job-portal-backend .
```

## Backup and Restore

### Database Backup

```bash
# Backup with timestamp
docker-compose exec -T oracle-db expdp sys/narasimha \
  FULL=Y \
  DUMPFILE=/backups/backup_$(date +%Y%m%d_%H%M%S).dmp

# Restore from backup
docker-compose exec -T oracle-db impdp sys/narasimha \
  FULL=Y \
  DUMPFILE=/backups/backup_20240101_120000.dmp
```

### Volume Backup

```bash
# Backup volume
docker run --rm \
  -v job-portal_oracle-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/oracle-data-backup.tar.gz -C /data .

# Restore volume
docker run --rm \
  -v job-portal_oracle-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/oracle-data-backup.tar.gz"
```

## Jenkins Credential Management

### Create Credentials via Jenkins UI

1. Go to Jenkins Dashboard
2. Manage Jenkins → Manage Credentials
3. Click Add Credentials
4. Select credential type:
   - **Username with password**: For Docker registry, Oracle DB
   - **Secret text**: For API keys, webhooks
   - **SSH Key**: For Git repositories

### Create Credentials via Jenkins CLI

```bash
# Create credentials using XML
echo '<hudson.model.PasswordParameterValue><name>ORACLE_PASSWORD</name><value>secret</value></hudson.model.PasswordParameterValue>' | \
  java -jar jenkins-cli.jar -s http://localhost:8080 update-credentials-by-xml -c system -d root

# List credentials
java -jar jenkins-cli.jar -s http://localhost:8080 list-credentials -c system -d root
```

## Common Workflows

### Full Development Cycle

```bash
# 1. Setup environment
make setup

# 2. Start services
make up

# 3. View logs while developing
make logs-backend

# 4. Run tests
make test

# 5. Lint code
make lint-backend

# 6. Rebuild after changes
make rebuild

# 7. Stop services
make down
```

### Deployment Workflow

```bash
# 1. Validate everything
make verify

# 2. Build images
make build

# 3. Stop current services
make down

# 4. Use production environment
ENV_FILE=.env.production make up

# 5. Check health
make health

# 6. Monitor
make monitor
```

### CI/CD Trigger

```bash
# In Jenkins or via CLI:
java -jar jenkins-cli.jar -s http://localhost:8080 build JobPortal-Pipeline \
  -p DEPLOYMENT_ENVIRONMENT=production \
  -p SKIP_TESTS=false \
  -p PUSH_TO_REGISTRY=true
```

---

**For more detailed information, see DOCKER_JENKINS_SETUP.md**
