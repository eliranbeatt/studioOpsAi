.PHONY: dev-up dev-down db-migrate db-seed api web

dev-up:
	docker-compose -f infra/docker-compose.yaml up -d

dev-down:
	docker-compose -f infra/docker-compose.yaml down

db-migrate:
	python infra/migrations/run_migrations.py

db-seed:
	cd packages/db && python seed.py

api:
	cd apps/api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && pnpm dev

logs:
	docker-compose -f infra/docker-compose.yaml logs -f

health:
	docker-compose -f infra/docker-compose.yaml ps
