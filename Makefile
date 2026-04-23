.PHONY: up down logs test lint migrate ollama-pull

# ── Docker ─────────────────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f backend worker

rebuild:
	docker compose up -d --build

# ── Development ────────────────────────────────────────────────────────────────
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-worker:
	cd backend && celery -A app.services.pipeline.celery_app worker --loglevel=info --concurrency=1

dev-frontend:
	cd frontend && npm run dev

# ── Database ───────────────────────────────────────────────────────────────────
migrate:
	cd backend && alembic upgrade head

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

# ── Testing ────────────────────────────────────────────────────────────────────
test:
	cd backend && pytest -v

lint:
	cd backend && python -m flake8 app/ tests/
	cd frontend && npm run lint

# ── Ollama model pull ──────────────────────────────────────────────────────────
ollama-pull:
	docker compose exec ollama ollama pull llama3.1:8b

# ── First-time setup ───────────────────────────────────────────────────────────
setup:
	cp .env.example .env
	docker compose up -d postgres redis minio ollama
	sleep 10
	$(MAKE) migrate
	$(MAKE) ollama-pull
	@echo "✅ Setup complete! Run 'make up' to start all services."
