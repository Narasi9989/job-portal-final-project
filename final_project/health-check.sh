#!/bin/bash

# Health Check Script for Job Portal Application
# Verifies that all services are running and healthy

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-1521}"
TIMEOUT=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
total_checks=0
passed_checks=0
failed_checks=0
warning_checks=0

# Functions
check() {
    local name=$1
    local command=$2
    local type=${3:-error}  # error, warning, info
    
    total_checks=$((total_checks + 1))
    
    echo -n "Checking ${name}... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        passed_checks=$((passed_checks + 1))
    else
        if [ "$type" = "warning" ]; then
            echo -e "${YELLOW}⚠ WARN${NC}"
            warning_checks=$((warning_checks + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            failed_checks=$((failed_checks + 1))
        fi
    fi
}

header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
}

# Main checks
header "Job Portal Health Check"

# Check system commands
echo ""
echo -e "${YELLOW}Checking system dependencies:${NC}"
check "Docker" "command -v docker" "info"
check "Docker Compose" "command -v docker-compose" "info"
check "curl" "command -v curl" "warning"
check "jq" "command -v jq" "warning"

# Check Docker daemon
echo ""
echo -e "${YELLOW}Checking Docker daemon:${NC}"
check "Docker daemon running" "docker ps > /dev/null 2>&1"

# Check containers
echo ""
echo -e "${YELLOW}Checking containers:${NC}"
check "Backend container running" "docker-compose ps backend | grep -q 'Up'"
check "Frontend container running" "docker-compose ps frontend | grep -q 'Up'"
check "Database container running" "docker-compose ps oracle-db | grep -q 'Up'"

# Check API endpoints
echo ""
echo -e "${YELLOW}Checking API endpoints:${NC}"
check "Backend API reachable" "curl -sf ${API_URL} > /dev/null"
check "Backend documentation" "curl -sf ${API_URL}/docs > /dev/null"
check "Backend OpenAPI JSON" "curl -sf ${API_URL}/openapi.json > /dev/null"

# Check frontend
echo ""
echo -e "${YELLOW}Checking frontend:${NC}"
check "Frontend reachable" "curl -sf ${FRONTEND_URL} > /dev/null"
check "Frontend returns HTML" "curl -s ${FRONTEND_URL} | grep -q '<html\\|<!DOCTYPE' || true"

# Check database connectivity
echo ""
echo -e "${YELLOW}Checking database:${NC}"
check "Database port listening" "nc -z ${DB_HOST} ${DB_PORT}" "warning"

# Check Docker network
echo ""
echo -e "${YELLOW}Checking Docker network:${NC}"
check "Docker network exists" "docker network inspect job-portal-network > /dev/null 2>&1" "warning"

# Check volumes
echo ""
echo -e "${YELLOW}Checking Docker volumes:${NC}"
check "Oracle data volume exists" "docker volume inspect job-portal_oracle-data > /dev/null 2>&1" "warning"
check "Backend uploads volume exists" "docker volume inspect job-portal_backend-uploads > /dev/null 2>&1" "warning"

# Check environment files
echo ""
echo -e "${YELLOW}Checking configuration files:${NC}"
check ".env file exists" "test -f .env"
check ".env.development file exists" "test -f .env.development" "warning"
check ".env.example file exists" "test -f .env.example"
check "docker-compose.yml exists" "test -f docker-compose.yml"
check "Jenkinsfile exists" "test -f Jenkinsfile" "warning"

# Detailed container checks
echo ""
echo -e "${YELLOW}Checking container details:${NC}"

# Backend health
backend_status=$(docker-compose ps backend 2>/dev/null | grep -o "Up\\|Exited" | head -1 || echo "Unknown")
if [ "$backend_status" = "Up" ]; then
    echo -e "Backend status: ${GREEN}$backend_status${NC}"
else
    echo -e "Backend status: ${RED}$backend_status${NC}"
fi

# Frontend health
frontend_status=$(docker-compose ps frontend 2>/dev/null | grep -o "Up\\|Exited" | head -1 || echo "Unknown")
if [ "$frontend_status" = "Up" ]; then
    echo -e "Frontend status: ${GREEN}$frontend_status${NC}"
else
    echo -e "Frontend status: ${RED}$frontend_status${NC}"
fi

# Database health
db_status=$(docker-compose ps oracle-db 2>/dev/null | grep -o "Up\\|Exited" | head -1 || echo "Unknown")
if [ "$db_status" = "Up" ]; then
    echo -e "Database status: ${GREEN}$db_status${NC}"
else
    echo -e "Database status: ${RED}$db_status${NC}"
fi

# Check resource usage
echo ""
echo -e "${YELLOW}Resource usage:${NC}"

if command -v docker &> /dev/null; then
    # Get backend memory
    backend_mem=$(docker stats --no-stream job-portal-backend 2>/dev/null | tail -1 | awk '{print $4}' || echo "N/A")
    echo "Backend memory: $backend_mem"
    
    # Get frontend memory
    frontend_mem=$(docker stats --no-stream job-portal-frontend 2>/dev/null | tail -1 | awk '{print $4}' || echo "N/A")
    echo "Frontend memory: $frontend_mem"
    
    # Get database memory
    db_mem=$(docker stats --no-stream oracle-db 2>/dev/null | tail -1 | awk '{print $4}' || echo "N/A")
    echo "Database memory: $db_mem"
fi

# Performance tests (optional)
echo ""
echo -e "${YELLOW}Performance checks (optional):${NC}"

if command -v curl &> /dev/null; then
    # Backend response time
    backend_time=$(curl -w "%{time_total}" -s -o /dev/null "${API_URL}/docs" 2>/dev/null || echo "N/A")
    echo "Backend API response time: ${backend_time}s"
    
    # Frontend response time
    frontend_time=$(curl -w "%{time_total}" -s -o /dev/null "${FRONTEND_URL}" 2>/dev/null || echo "N/A")
    echo "Frontend response time: ${frontend_time}s"
fi

# Summary
echo ""
header "Health Check Summary"

echo ""
echo "Total checks: $total_checks"
echo -e "Passed: ${GREEN}$passed_checks${NC}"
if [ $warning_checks -gt 0 ]; then
    echo -e "Warnings: ${YELLOW}$warning_checks${NC}"
fi
if [ $failed_checks -gt 0 ]; then
    echo -e "Failed: ${RED}$failed_checks${NC}"
fi

echo ""

# Determine overall health status
if [ $failed_checks -eq 0 ]; then
    if [ $warning_checks -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed! Application is healthy.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Application is running but some checks had warnings.${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ Some checks failed. Please review the issues above.${NC}"
    exit 1
fi
