.PHONY: help up up-build up-prod up-prod-build down down-prod down-volumes \
        logs logs-django logs-celery logs-db logs-redis \
        shell shell-plus migrate makemigrations createsuperuser collectstatic \
        db-shell db-backup db-restore redis-cli redis-flush \
        celery-shell celery-purge celery-status \
        test test-coverage lint lint-fix format format-check mypy check fix \
        clean clean-all restart health monitor setup setup-env \
        install sync lock add

DC      = docker compose
DEV     = $(DC) --profile dev
PROD    = $(DC) --profile prod
UV      = uv

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Dev lifecycle ─────────────────────────────────────────────────────────────
up: ## Start dev environment (db, redis, django, celery, beat, flower)
	$(DEV) up -d

up-build: ## Build images then start dev environment
	$(DEV) up -d --build

down: ## Stop dev environment
	$(DEV) down

down-volumes: ## Stop dev environment and remove all volumes
	$(DC) down -v

# ── Prod lifecycle ────────────────────────────────────────────────────────────
up-prod: ## Start prod environment (db, redis, web, worker, scheduler, nginx)
	$(PROD) up -d

up-prod-build: ## Build images then start prod environment
	$(PROD) up -d --build

down-prod: ## Stop prod environment
	$(PROD) down

# ── Logs ──────────────────────────────────────────────────────────────────────
logs: ## Tail logs for all running services
	$(DC) logs -f

logs-django: ## Tail django / web service logs
	$(DC) logs -f django web 2>/dev/null || $(DC) logs -f django 2>/dev/null || $(DC) logs -f web

logs-celery: ## Tail celery / worker logs
	$(DC) logs -f celery worker 2>/dev/null || true

logs-db: ## Tail database logs
	$(DC) logs -f db

logs-redis: ## Tail redis logs
	$(DC) logs -f redis

# ── Django management ─────────────────────────────────────────────────────────
shell: ## Open Django shell (dev)
	$(DEV) exec django python manage.py shell

shell-plus: ## Open Django shell_plus (dev)
	$(DEV) exec django python manage.py shell_plus

migrate: ## Run migrations (dev)
	$(DEV) exec django python manage.py migrate

makemigrations: ## Create migrations (dev)
	$(DEV) exec django python manage.py makemigrations

createsuperuser: ## Create superuser (dev)
	$(DEV) exec django python manage.py createsuperuser

collectstatic: ## Collect static files (dev)
	$(DEV) exec django python manage.py collectstatic --noinput

# ── Database ──────────────────────────────────────────────────────────────────
db-shell: ## Connect to Postgres shell
	$(DC) exec db psql -U $${DB_USER:-postgres} -d $${DB_NAME:-ecommerce_db}

db-backup: ## Dump database to timestamped SQL file
	$(DC) exec db pg_dump -U $${DB_USER:-postgres} $${DB_NAME:-ecommerce_db} \
	  > backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database (usage: make db-restore FILE=backup.sql)
	$(DC) exec -T db psql -U $${DB_USER:-postgres} -d $${DB_NAME:-ecommerce_db} < $(FILE)

# ── Redis ─────────────────────────────────────────────────────────────────────
redis-cli: ## Open Redis CLI
	$(DC) exec redis redis-cli

redis-flush: ## Flush all Redis keys
	$(DC) exec redis redis-cli FLUSHALL

# ── Celery ────────────────────────────────────────────────────────────────────
celery-status: ## Show Celery worker status (dev)
	$(DEV) exec celery celery -A api status

celery-purge: ## Purge all queued Celery tasks (dev)
	$(DEV) exec celery celery -A api purge -f

# ── Testing & quality ─────────────────────────────────────────────────────────
test: ## Run test suite (dev container)
	$(DEV) exec django $(UV) run python -m pytest

test-coverage: ## Run tests with HTML coverage report
	$(DEV) exec django $(UV) run python -m pytest --cov=. --cov-report=html

lint: ## Lint with Ruff
	$(DEV) exec django $(UV) run ruff check .

lint-fix: ## Lint and auto-fix with Ruff
	$(DEV) exec django $(UV) run ruff check --fix .

format: ## Format with Ruff
	$(DEV) exec django $(UV) run ruff format .

format-check: ## Check formatting (CI)
	$(DEV) exec django $(UV) run ruff format --check .

mypy: ## Type-check with mypy
	$(DEV) exec django $(UV) run mypy .

check: lint format-check test ## Run all checks (lint + format + tests)

fix: lint-fix format ## Auto-fix all linting and formatting issues

# ── Package management ────────────────────────────────────────────────────────
install: ## Install dependencies with uv
	$(UV) pip install -e .

sync: ## Sync dependencies from lockfile
	$(UV) sync

lock: ## Regenerate uv.lock
	$(UV) lock

add: ## Add a dependency (usage: make add PACKAGE=foo==1.2.3)
	$(UV) add $(PACKAGE)

# ── Utilities ─────────────────────────────────────────────────────────────────
restart: ## Restart all dev services
	$(DEV) restart

health: ## Check health endpoints
	@echo "API:    $$(curl -sf http://localhost:8000/health/ && echo OK || echo DOWN)"
	@echo "Flower: $$(curl -sf http://localhost:5555/ && echo OK || echo DOWN)"

monitor: ## Print dashboard URLs
	@echo "Django admin : http://localhost:8000/admin"
	@echo "API docs     : http://localhost:8000/api/docs"
	@echo "Flower       : http://localhost:5555"

clean: ## Remove stopped containers and dangling images
	docker system prune -f

clean-all: ## Remove all unused Docker resources (images, volumes, networks)
	docker system prune -a -f
	docker volume prune -f

# ── First-run setup ───────────────────────────────────────────────────────────
setup-env: ## Copy env.example → .env (skips if .env exists)
	@[ -f .env ] && echo ".env already exists" || (cp .env.example .env && echo "Created .env — edit it before running make up")

setup: setup-env up-build ## Full first-run: copy env, build images, start dev, run migrations
	@echo "Waiting for services..."
	@sleep 5
	$(MAKE) migrate
	@echo ""
	@echo "Done!  Visit http://localhost:8000/api/docs"
