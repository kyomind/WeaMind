dev-up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

tree:
	zsh scripts/gen_tree.sh
