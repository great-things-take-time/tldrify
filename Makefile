.PHONY: help install dev-install docker-up docker-down db-init db-migrate db-upgrade test lint format run clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make db-init       - Initialize database tables"
	@echo "  make db-migrate    - Create new migration"
	@echo "  make db-upgrade    - Apply migrations"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make run           - Run FastAPI server"
	@echo "  make clean         - Clean cache files"

install:
	uv pip install -e .

dev-install:
	uv pip install -e ".[dev]"

docker-up:
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@docker-compose ps

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

db-init:
	source .venv/bin/activate && python scripts/init_db.py

db-migrate:
	source .venv/bin/activate && alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	source .venv/bin/activate && alembic upgrade head

db-downgrade:
	source .venv/bin/activate && alembic downgrade -1

test:
	source .venv/bin/activate && pytest tests/ -v

lint:
	source .venv/bin/activate && ruff check src/
	source .venv/bin/activate && mypy src/

format:
	source .venv/bin/activate && black src/
	source .venv/bin/activate && ruff check --fix src/

run:
	source .venv/bin/activate && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

celery:
	source .venv/bin/activate && celery -A src.services.celery_app worker --loglevel=info

flower:
	source .venv/bin/activate && celery -A src.services.celery_app flower

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete