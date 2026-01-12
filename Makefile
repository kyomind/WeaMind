APP_SERVICE=app

.PHONY: dev-up clean up down deploy migrate revision rollback tree check prune setup-prod upgrade-pyright sync-instructions export-docs clean-docs worktree-add worktree-list worktree-remove worktree-clean update-liff-version update-static-version changelog-status changelog-prepare changelog-release changelog-help upload upload-list upload-delete security-bandit security-audit security-all

# === Container & Image Management ===
dev-up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

clean:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v

setup-prod:
	docker volume create wea-db-data-prod
	docker network create wea-net || true

up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build

down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

deploy:
	@echo "🚀 開始部署..."
	@echo "📥 拉取最新 image..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml pull app
	@echo "📦 啟動容器..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "⏳ 等待資料庫服務啟動..."
	@until docker compose exec db pg_isready -U wea_bot -d weamind -q; do \
		echo "等待資料庫準備中..."; \
		sleep 2; \
	done
	@echo "🔄 執行資料庫遷移..."
	@if docker compose exec $(APP_SERVICE) uv run alembic upgrade head; then \
		echo "✅ 資料庫遷移完成"; \
	else \
		echo "⚠️  資料庫遷移失敗，請檢查是否有新的遷移檔案或資料庫連線"; \
	fi
	@echo "✅ 部署完成！"

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

# === LIFF Development ===
update-liff-version:
	@echo "🔄 Updating LIFF version..."
	@zsh scripts/update_liff_version.sh

# === Static Pages Cache Management ===
update-static-version:
	@echo "🔄 Updating static pages version..."
	@zsh scripts/update_static_pages_version.sh

# === Version & Release Management ===
changelog-status:
	@zsh scripts/changelog.sh status

changelog-prepare:
	@zsh scripts/changelog.sh prepare $(VERSION)

changelog-release:
	@zsh scripts/changelog.sh release $(VERSION)

changelog-help:
	@zsh scripts/changelog.sh quick-help

# === Rich Menu Management ===
upload:
	@echo "🚀 Uploading Rich Menu..."
	@if [ -z "$(IMAGE)" ]; then \
		echo "❌ 錯誤：請指定圖片路徑"; \
		echo "使用方式：make upload IMAGE=path/to/rich_menu.png"; \
		exit 1; \
	fi
	@uv run python scripts/rich_menu_manager.py create --image "$(IMAGE)" --set-default

upload-list:
	@echo "📋 列出所有 Rich Menu..."
	@uv run python scripts/rich_menu_manager.py list

upload-delete:
	@echo "🗑️ 刪除 Rich Menu..."
	@if [ -z "$(ID)" ]; then \
		echo "❌ 錯誤：請指定 Rich Menu ID"; \
		echo "使用方式：make upload-delete ID=rich_menu_id"; \
		exit 1; \
	fi
	@uv run python scripts/rich_menu_manager.py delete --rich-menu-id "$(ID)"

# === Security Scanning ===
security-bandit:
	@echo "🔒 執行 Bandit 安全掃描..."
	@mkdir -p security-reports
	@uv run bandit -c bandit.yaml -r app -f json -o security-reports/bandit-report.json
	@uv run bandit -c bandit.yaml -r app

security-audit:
	@echo "🔍 執行 pip-audit 依賴弱點掃描..."
	@mkdir -p security-reports
	@uv run pip-audit --format=json --output=security-reports/pip-audit-report.json --ignore-vuln=GHSA-xqrq-4mgf-ff32 --ignore-vuln=GHSA-4xh5-x5gv-qwph
	@uv run pip-audit --ignore-vuln=GHSA-xqrq-4mgf-ff32 --ignore-vuln=GHSA-4xh5-x5gv-qwph

security-all:
	@echo "🛡️ 執行完整安全掃描..."
	@$(MAKE) security-bandit
	@$(MAKE) security-audit
	@echo "✅ 安全掃描完成！"
