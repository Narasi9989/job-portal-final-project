#!/bin/bash

# Job Portal Production Deployment Script
# This script automates the deployment of the Job Portal application to production

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="job-portal"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
DEPLOYMENT_ENVIRONMENT="production"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
LOG_DIR="${LOG_DIR:-./logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_file="${LOG_DIR}/deployment_${TIMESTAMP}.log"
mkdir -p "${LOG_DIR}"

log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "${log_file}"
}

log_success() {
    log "${GREEN}✓ $1${NC}"
}

log_error() {
    log "${RED}✗ $1${NC}"
}

log_info() {
    log "${BLUE}ℹ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠ $1${NC}"
}

# Error handling
error_exit() {
    log_error "Deployment failed: $1"
    log_info "Check logs at: ${log_file}"
    exit 1
}

# Prerequisites check
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed"
    fi
    log_success "Docker is installed: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed"
    fi
    log_success "Docker Compose is installed: $(docker-compose --version)"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        error_exit "Git is not installed"
    fi
    log_success "Git is installed: $(git --version | head -1)"
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        log_warning "curl is not installed, some features may not work"
    fi
}

# Backup current deployment
backup_deployment() {
    log_info "Creating backup of current deployment..."
    
    mkdir -p "${BACKUP_DIR}"
    
    # Backup docker-compose volumes
    if docker-compose ps -q oracle-db > /dev/null 2>&1; then
        log_info "Backing up Oracle database..."
        
        docker-compose exec -T oracle-db expdp sys/"${ORACLE_PASSWORD}" \
            FULL=Y \
            DUMPFILE=/tmp/backup_${TIMESTAMP}.dmp \
            LOGFILE=/tmp/backup_${TIMESTAMP}.log \
            2>/dev/null || log_warning "Database backup via expdp failed"
        
        docker cp "$(docker-compose ps -q oracle-db)":/tmp/backup_${TIMESTAMP}.dmp \
            "${BACKUP_DIR}/oracle_backup_${TIMESTAMP}.dmp" || log_warning "Could not copy database backup"
        
        log_success "Database backed up to ${BACKUP_DIR}"
    fi
    
    # Backup volumes
    log_info "Backing up Docker volumes..."
    docker run --rm \
        -v ${PROJECT_NAME}_oracle-data:/data \
        -v "${BACKUP_DIR}":/backup \
        alpine tar czf "/backup/oracle-data_${TIMESTAMP}.tar.gz" -C /data . \
        2>/dev/null || log_warning "Volume backup failed"
    
    docker run --rm \
        -v ${PROJECT_NAME}_backend-uploads:/data \
        -v "${BACKUP_DIR}":/backup \
        alpine tar czf "/backup/backend-uploads_${TIMESTAMP}.tar.gz" -C /data . \
        2>/dev/null || log_warning "Uploads backup failed"
    
    log_success "Volumes backed up to ${BACKUP_DIR}"
}

# Update source code
update_source_code() {
    log_info "Updating source code..."
    
    # Pull latest code
    log_info "Pulling latest code from repository..."
    git pull origin main || error_exit "Failed to pull latest code"
    
    log_success "Source code updated"
    log_info "Latest commit: $(git log -1 --oneline)"
}

# Load environment
load_environment() {
    log_info "Loading environment configuration..."
    
    if [ ! -f ".env.${DEPLOYMENT_ENVIRONMENT}" ]; then
        error_exit "Environment file .env.${DEPLOYMENT_ENVIRONMENT} not found"
    fi
    
    set -a
    source ".env.${DEPLOYMENT_ENVIRONMENT}"
    set +a
    
    # Validate required variables
    required_vars=("ORACLE_USER" "ORACLE_PASSWORD" "ORACLE_HOST" "ORACLE_PORT" "VITE_API_URL")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error_exit "Required environment variable $var is not set"
        fi
    done
    
    log_success "Environment loaded successfully"
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images..."
    
    # Build backend
    log_info "Building backend image..."
    docker build \
        --tag "${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${TIMESTAMP}" \
        --tag "${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:latest" \
        --build-arg VERSION="1.0.0" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        ./backend_fastapi || error_exit "Failed to build backend image"
    
    log_success "Backend image built: ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:latest"
    
    # Build frontend
    log_info "Building frontend image..."
    docker build \
        --tag "${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:${TIMESTAMP}" \
        --tag "${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:latest" \
        --build-arg VERSION="1.0.0" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        ./goskill-frontend || error_exit "Failed to build frontend image"
    
    log_success "Frontend image built: ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:latest"
}

# Push Docker images to registry
push_docker_images() {
    log_info "Pushing Docker images to registry..."
    
    if [ -z "${DOCKER_REGISTRY_USERNAME}" ] || [ -z "${DOCKER_REGISTRY_PASSWORD}" ]; then
        log_warning "Docker registry credentials not provided, skipping push"
        return
    fi
    
    log_info "Logging in to Docker registry..."
    echo "${DOCKER_REGISTRY_PASSWORD}" | docker login -u "${DOCKER_REGISTRY_USERNAME}" --password-stdin "${DOCKER_REGISTRY}" || \
        log_warning "Docker login failed"
    
    log_info "Pushing backend image..."
    docker push "${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:${TIMESTAMP}" || log_warning "Failed to push backend image"
    docker push "${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:latest" || log_warning "Failed to push backend latest tag"
    
    log_info "Pushing frontend image..."
    docker push "${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:${TIMESTAMP}" || log_warning "Failed to push frontend image"
    docker push "${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:latest" || log_warning "Failed to push frontend latest tag"
    
    log_success "Docker images pushed to registry"
}

# Stop current services
stop_services() {
    log_info "Stopping current services..."
    
    docker-compose --env-file ".env.${DEPLOYMENT_ENVIRONMENT}" stop || log_warning "Failed to stop services"
    
    log_success "Services stopped"
}

# Start new services
start_services() {
    log_info "Starting services with new images..."
    
    docker-compose --env-file ".env.${DEPLOYMENT_ENVIRONMENT}" up -d || \
        error_exit "Failed to start services"
    
    log_success "Services started"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    local max_retries=30
    local retry=0
    
    # Wait for backend
    log_info "Checking backend health..."
    while [ $retry -lt $max_retries ]; do
        if curl -sf http://localhost:8000/docs > /dev/null 2>&1; then
            log_success "Backend is healthy"
            break
        fi
        
        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            log_info "Attempt $retry/$max_retries - Waiting for backend..."
            sleep 2
        fi
    done
    
    if [ $retry -eq $max_retries ]; then
        error_exit "Backend health check failed"
    fi
    
    # Reset retry counter
    retry=0
    
    # Wait for frontend
    log_info "Checking frontend health..."
    while [ $retry -lt $max_retries ]; do
        if curl -sf http://localhost:3000 > /dev/null 2>&1; then
            log_success "Frontend is healthy"
            break
        fi
        
        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            log_info "Attempt $retry/$max_retries - Waiting for frontend..."
            sleep 2
        fi
    done
    
    if [ $retry -eq $max_retries ]; then
        error_exit "Frontend health check failed"
    fi
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test backend API
    log_info "Testing backend API..."
    if curl -sf http://localhost:8000/docs > /dev/null; then
        log_success "Backend API test passed"
    else
        error_exit "Backend API test failed"
    fi
    
    # Test frontend
    log_info "Testing frontend..."
    if curl -sf http://localhost:3000 > /dev/null; then
        log_success "Frontend test passed"
    else
        error_exit "Frontend test failed"
    fi
}

# Send notifications
send_notifications() {
    local status=$1
    local message=$2
    
    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL}" ]; then
        local color="good"
        local emoji="✅"
        if [ "${status}" = "failure" ]; then
            color="danger"
            emoji="❌"
        fi
        
        curl -X POST "${SLACK_WEBHOOK_URL}" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\":\"${emoji} ${message}\",
                \"color\":\"${color}\",
                \"fields\":[
                    {\"title\":\"Environment\",\"value\":\"${DEPLOYMENT_ENVIRONMENT}\",\"short\":true},
                    {\"title\":\"Timestamp\",\"value\":\"$(date)\",\"short\":true},
                    {\"title\":\"Commit\",\"value\":\"$(git rev-parse --short HEAD)\",\"short\":true}
                ]
            }" 2>/dev/null || true
    fi
    
    # Email notification
    if [ -n "${NOTIFICATION_EMAIL}" ] && command -v mail &> /dev/null; then
        {
            echo "Job Portal Deployment ${status^^}"
            echo "================================"
            echo "Status: ${status^^}"
            echo "Environment: ${DEPLOYMENT_ENVIRONMENT}"
            echo "Timestamp: $(date)"
            echo "Commit: $(git log -1 --oneline)"
            echo ""
            echo "Message: ${message}"
            echo ""
            echo "Logs: ${log_file}"
        } | mail -s "[${status^^}] Job Portal Deployment" "${NOTIFICATION_EMAIL}"
    fi
}

# Rollback to previous version
rollback() {
    log_warning "Rolling back to previous version..."
    
    # Stop current services
    docker-compose --env-file ".env.${DEPLOYMENT_ENVIRONMENT}" down || true
    
    # Restore from backup
    if [ -f "${BACKUP_DIR}/oracle_backup_${TIMESTAMP}.dmp" ]; then
        log_info "Restoring database from backup..."
        
        # Start database container
        docker-compose --env-file ".env.${DEPLOYMENT_ENVIRONMENT}" up -d oracle-db
        sleep 30
        
        docker-compose exec -T oracle-db impdp sys/"${ORACLE_PASSWORD}" \
            FULL=Y \
            DUMPFILE=/tmp/backup_${TIMESTAMP}.dmp \
            LOGFILE=/tmp/rollback_${TIMESTAMP}.log || log_warning "Database restore failed"
    fi
    
    # Start all services with previous image
    docker-compose --env-file ".env.${DEPLOYMENT_ENVIRONMENT}" up -d
    
    log_success "Rollback completed"
}

# Display summary
display_summary() {
    log_info "Deployment Summary:"
    echo ""
    echo "Project: ${PROJECT_NAME}"
    echo "Environment: ${DEPLOYMENT_ENVIRONMENT}"
    echo "Deployment Time: ${TIMESTAMP}"
    echo "Backend Image: ${DOCKER_REGISTRY}/${PROJECT_NAME}-backend:latest"
    echo "Frontend Image: ${DOCKER_REGISTRY}/${PROJECT_NAME}-frontend:latest"
    echo "Git Commit: $(git log -1 --oneline)"
    echo "Log File: ${log_file}"
    echo ""
    echo "Access URLs:"
    echo "  Backend API: http://localhost:8000/docs"
    echo "  Frontend: http://localhost:3000"
    echo ""
    echo "Backup Location: ${BACKUP_DIR}"
}

# Main execution
main() {
    log_info "Starting Job Portal Production Deployment"
    log_info "Deployment Timestamp: ${TIMESTAMP}"
    
    # Run deployment steps
    check_prerequisites
    load_environment
    
    # Confirm before proceeding
    log_warning "This will deploy to PRODUCTION environment"
    read -p "Continue with deployment? (yes/no) " -n 3 -r
    echo
    if [[ ! $REPLY =~ ^yes$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    
    # Execute deployment
    backup_deployment
    update_source_code
    build_docker_images
    push_docker_images
    stop_services
    start_services
    wait_for_health
    run_smoke_tests
    
    log_success "Deployment completed successfully!"
    display_summary
    send_notifications "success" "Job Portal deployment completed successfully to ${DEPLOYMENT_ENVIRONMENT}"
    
    log_info "For rollback: $0 rollback"
}

# Handle rollback command
if [ "${1}" = "rollback" ]; then
    load_environment
    rollback
    send_notifications "failure" "Job Portal deployment rolled back"
    exit 0
fi

# Execute main deployment
main
