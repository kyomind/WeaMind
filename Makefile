APP_SERVICE=app

.PHONY: dev-up dev-down up down deploy migrate revision rollback tree check prune
# === Container & Image Management ===
dev-up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build

down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

deploy:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# === Database Migration ===
migrate:
	docker compose exec $(APP_SERVICE) uv run alembic upgrade head

revision:
	docker compose exec $(APP_SERVICE) uv run alembic revision --autogenerate -m "$(shell git rev-parse --abbrev-ref HEAD)_$(shell date +%Y%m%d_%H%M%S)"

rollback:
	docker compose exec $(APP_SERVICE) uv run alembic downgrade -1

# === Local Utility Scripts ===
tree:
	zsh scripts/gen_tree.sh

check:
	zsh scripts/cleanup_local_branches_preview.sh

prune:
	zsh scripts/cleanup_local_branches.sh
