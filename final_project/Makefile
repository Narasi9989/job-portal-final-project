.PHONY: help build up down logs clean rebuild health test lint build-backend build-frontend push restart

# Default environment file
ENV_FILE ?= .env.development

# Docker Compose command
DC := docker-compose --env-file $(ENV_FILE)

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

.DEFAULT_GOAL := help

help: ## Display this help screen
	@echo "$(GREEN)Job Portal Docker & Jenkins CI/CD Makefile$(NC)"
	@echo "$(YELLOW)Usage: make [target] ENV_FILE=.env.production$(NC)"
	@echo ""
	@echo "$(GREEN)Docker Compose Targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build Docker images (backend, frontend)
	@echo "$(GREEN)Building Docker images...$(NC)"
	$(DC) build --no-cache

build-backend: ## Build only backend Docker image
	@echo "$(GREEN)Building backend image...$(NC)"
	docker build -t job-portal-backend:latest ./backend_fastapi

build-frontend: ## Build only frontend Docker image
	@echo "$(GREEN)Building frontend image...$(NC)"
	docker build -t job-portal-frontend:latest ./goskill-frontend

up: ## Start all services
	@echo "$(GREEN)Starting services...$(NC)"
	$(DC) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@make health

down: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	$(DC) down --remove-orphans
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: down up ## Restart all services

logs: ## View logs from all services
	$(DC) logs -f

logs-backend: ## View backend logs
	$(DC) logs -f backend

logs-frontend: ## View frontend logs
	$(DC) logs -f frontend

logs-db: ## View database logs
	$(DC) logs -f oracle-db

status: ## Show container status
	@echo "$(YELLOW)Container Status:$(NC)"
	@$(DC) ps

health: ## Check health of all services
	@echo "$(YELLOW)Checking service health...$(NC)"
	@echo ""
	@echo "$(GREEN)Backend:$(NC)"
	@curl -s -f http://localhost:8000/docs > /dev/null && echo "  ✓ Healthy" || echo "  ✗ Unhealthy"
	@echo ""
	@echo "$(GREEN)Frontend:$(NC)"
	@curl -s -f http://localhost:3000 > /dev/null && echo "  ✓ Healthy" || echo "  ✗ Unhealthy"
	@echo ""

test: ## Run tests inside Docker containers
	@echo "$(GREEN)Running tests...$(NC)"
	$(DC) exec -T backend pytest --cov=. --cov-report=html

lint-backend: ## Lint backend code
	@echo "$(GREEN)Linting backend code...$(NC)"
	$(DC) exec backend python -m flake8 . --max-line-length=120 --ignore=E501,W503 --exclude=venv

lint-frontend: ## Lint frontend code
	@echo "$(GREEN)Linting frontend code...$(NC)"
	$(DC) exec frontend npm run lint 2>/dev/null || echo "No lint script defined"

bash-backend: ## Open bash in backend container
	@echo "$(GREEN)Opening bash in backend container...$(NC)"
	$(DC) exec backend bash

bash-frontend: ## Open bash in frontend container
	@echo "$(GREEN)Opening bash in frontend container...$(NC)"
	$(DC) exec frontend sh

bash-db: ## Open sqlplus in database container
	@echo "$(GREEN)Opening sqlplus in database container...$(NC)"
	$(DC) exec -T oracle-db sqlplus -S sys/narasimha@localhost:1521/XE as sysdba

clean: ## Remove containers and volumes
	@echo "$(RED)Removing containers and volumes...$(NC)"
	$(DC) down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-volumes: ## Remove only volumes (keeps images)
	@echo "$(RED)Removing volumes...$(NC)"
	docker volume prune -f
	@echo "$(GREEN)✓ Volumes removed$(NC)"

clean-images: ## Remove Docker images
	@echo "$(RED)Removing Docker images...$(NC)"
	docker rmi job-portal-backend job-portal-frontend
	@echo "$(GREEN)✓ Images removed$(NC)"

clean-system: ## Remove all Docker resources (careful!)
	@echo "$(RED)WARNING: This will remove all Docker images, containers, and volumes!$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -af; \
		echo "$(GREEN)✓ System cleaned$(NC)"; \
	fi

rebuild: clean build up ## Clean and rebuild everything

validate-env: ## Validate environment file
	@echo "$(YELLOW)Validating environment variables...$(NC)"
	@test -f $(ENV_FILE) && echo "$(GREEN)✓ Environment file exists: $(ENV_FILE)$(NC)" || echo "$(RED)✗ Environment file not found: $(ENV_FILE)$(NC)"
	@grep -q "ORACLE_USER" $(ENV_FILE) && echo "$(GREEN)✓ ORACLE_USER is set$(NC)" || echo "$(RED)✗ ORACLE_USER not set$(NC)"
	@grep -q "ORACLE_PASSWORD" $(ENV_FILE) && echo "$(GREEN)✓ ORACLE_PASSWORD is set$(NC)" || echo "$(RED)✗ ORACLE_PASSWORD not set$(NC)"
	@grep -q "VITE_API_URL" $(ENV_FILE) && echo "$(GREEN)✓ VITE_API_URL is set$(NC)" || echo "$(RED)✗ VITE_API_URL not set$(NC)"

push: ## Push Docker images to registry
	@echo "$(GREEN)Pushing Docker images to registry...$(NC)"
	docker push job-portal-backend:latest
	docker push job-portal-frontend:latest
	@echo "$(GREEN)✓ Images pushed$(NC)"

version: ## Show version information
	@echo "$(YELLOW)Version Information:$(NC)"
	@echo "Docker version: $$(docker --version)"
	@echo "Docker Compose version: $$(docker-compose --version)"
	@echo "Environment: $$(grep ENV_FILE=$(ENV_FILE) /dev/null || echo $(ENV_FILE))"

verify: ## Verify project structure and dependencies
	@echo "$(GREEN)Verifying project structure...$(NC)"
	@test -f backend_fastapi/main.py && echo "$(GREEN)✓ Backend main.py found$(NC)" || echo "$(RED)✗ Backend main.py not found$(NC)"
	@test -f backend_fastapi/requirements.txt && echo "$(GREEN)✓ Backend requirements.txt found$(NC)" || echo "$(RED)✗ Backend requirements.txt not found$(NC)"
	@test -f goskill-frontend/package.json && echo "$(GREEN)✓ Frontend package.json found$(NC)" || echo "$(RED)✗ Frontend package.json not found$(NC)"
	@test -f docker-compose.yml && echo "$(GREEN)✓ docker-compose.yml found$(NC)" || echo "$(RED)✗ docker-compose.yml not found$(NC)"
	@test -f Jenkinsfile && echo "$(GREEN)✓ Jenkinsfile found$(NC)" || echo "$(RED)✗ Jenkinsfile not found$(NC)"
	@test -f .env.example && echo "$(GREEN)✓ .env.example found$(NC)" || echo "$(RED)✗ .env.example not found$(NC)"

setup: ## Initial setup - copy env file and verify
	@echo "$(GREEN)Setting up environment...$(NC)"
	@if [ ! -f .env.development ]; then \
		cp .env.example .env.development; \
		echo "$(GREEN)✓ Created .env.development from .env.example$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env.development already exists$(NC)"; \
	fi
	@make verify
	@echo "$(GREEN)✓ Setup complete! Run 'make up' to start services$(NC)"

backup-db: ## Backup Oracle database
	@echo "$(GREEN)Backing up Oracle database...$(NC)"
	@mkdir -p backups
	$(DC) exec -T oracle-db expdp sys/narasimha FULL=Y DUMPFILE=/backups/backup_$$(date +%Y%m%d_%H%M%S).dmp
	@echo "$(GREEN)✓ Database backed up$(NC)"

restore-db: ## Restore Oracle database
	@echo "$(RED)Restoring Oracle database...$(NC)"
	@read -p "Enter backup file name: " backup_file; \
	$(DC) exec -T oracle-db impdp sys/narasimha FULL=Y DUMPFILE=/backups/$$backup_file
	@echo "$(GREEN)✓ Database restored$(NC)"

monitor: ## Monitor resource usage
	@echo "$(YELLOW)Monitoring Docker resource usage...$(NC)"
	docker stats --no-stream

prune: ## Clean up unused Docker resources
	@echo "$(YELLOW)Pruning Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Pruned unused resources$(NC)"

jenkins-setup: ## Run Jenkins setup script
	@echo "$(GREEN)Running Jenkins setup...$(NC)"
	@bash jenkins-setup.sh

jenkins-logs: ## View Jenkins container logs
	docker logs jenkins | tail -50

.PHONY: test-all
test-all: lint-backend lint-frontend test ## Run all tests

install-dependencies: ## Install local dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	cd backend_fastapi && pip install -r requirements.txt
	cd goskill-frontend && npm install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	$(DC) exec backend python -m black . 2>/dev/null || echo "Black not installed"

security-scan: ## Scan Docker images for vulnerabilities
	@echo "$(GREEN)Scanning Docker images for vulnerabilities...$(NC)"
	docker scout cves job-portal-backend:latest
	docker scout cves job-portal-frontend:latest

docs: ## Open documentation
	@echo "$(GREEN)Opening Docker & Jenkins documentation...$(NC)"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open DOCKER_JENKINS_SETUP.md || \
	command -v open >/dev/null 2>&1 && open DOCKER_JENKINS_SETUP.md || \
	echo "Please open DOCKER_JENKINS_SETUP.md manually"
