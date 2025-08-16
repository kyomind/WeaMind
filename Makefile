APP_SERVICE=app

.PHONY: dev-up dev-down dev-clean up down deploy migrate revision rollback tree check prune setup-prod upgrade-pyright sync-instructions export-docs clean-docs worktree-add worktree-list worktree-remove worktree-clean
# === Container & Image Management ===
dev-up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

dev-clean:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v

setup-prod:
	docker volume create wea-db-data-prod
	docker network create wea-net || true

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

# === Package Management ===
upgrade-pyright:
	uv lock --upgrade-package pyright
	uv sync

# === Git Worktree Management ===
worktree-add:
	zsh scripts/worktree_add.sh

worktree-list:
	zsh scripts/worktree_list.sh

worktree-remove:
	zsh scripts/worktree_remove.sh

worktree-clean:
	zsh scripts/worktree_clean.sh

# === Local Utility Scripts ===
tree:
	zsh scripts/gen_tree.sh

check:
	zsh scripts/cleanup_local_branches_preview.sh

prune:
	zsh scripts/cleanup_local_branches.sh

sync-instructions:
	zsh scripts/sync_instructions.sh

export-docs:
	zsh scripts/export_branch_docs.sh

clean-docs:
	zsh scripts/clean_docs.sh
