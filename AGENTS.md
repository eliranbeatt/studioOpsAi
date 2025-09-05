# Repository Guidelines

## Project Structure & Module Organization
- `apps/api`: FastAPI service (routers, services, models). Tests live in `apps/api/tests`. Local config via `.env` / `.env.test`.
- `apps/web`: Next.js app under `src/` (`app/`, `components/`, `hooks/`, `types/`). Jest unit tests co-located (e.g., `PlanEditor.test.tsx`); Playwright E2E in `e2e-tests/`.
- `packages/`: Shared Python code (`db` migrations/seed, `schemas`, `clients`).
- `infra/`: Docker Compose and SQL migrations.
- `tests/`: Cross-app `unit/`, `integration/`, and `e2e/` suites.
- `Makefile`: Common dev shortcuts.

## Build, Test, and Development Commands
- `make dev-up` / `make dev-down`: Start/stop services in `infra/docker-compose.yaml`.
- `make api`: Run API (`uvicorn`) at `http://localhost:8000`.
- `make web`: Run Next.js dev server at `http://localhost:3000`.
- API tests: `cd apps/api && pytest` (coverage + HTML report via `pytest.ini`).
- Web tests: `cd apps/web && pnpm test` (Jest); `pnpm test:e2e` (Playwright).
- DB: `make db-migrate` (alembic), `make db-seed` (`packages/db/seed.py`).

## Coding Style & Naming Conventions
- Python: Black (88 cols), flake8, mypy (see `SuperClaude_Framework/pyproject.toml`). `snake_case` for files/functions; `PascalCase` for Pydantic/ORM models.
- TypeScript/React: ESLint + Next.js defaults. `PascalCase` components (e.g., `PlanEditor.tsx`), `camelCase` hooks/utils (e.g., `useMaterials.ts`). Tailwind in `globals.css`.

## Testing Guidelines
- API: Pytest configured in `apps/api/pytest.ini` with coverage (`--cov=apps/api`). Place tests under `apps/api/tests`.
- Web: Unit via Jest; E2E via Playwright (`apps/web/e2e-tests`). Prefer deterministic tests; mock HTTP with MSW where possible.
- Add tests for new/changed code and edge cases; include failing reproduction when fixing bugs.

## Commit & Pull Request Guidelines
- Commits: imperative, concise; optional scope prefix (e.g., `api: add vendors router`, `web: fix theme toggle`). Avoid WIP.
- PRs: clear summary, linked issues, setup/run notes, and evidence (screenshots for UI; `pytest -q` / `pnpm test` output). Include migration notes when DB changes.

## Security & Configuration
- Copy `.env.example` to `.env`. Do not commit secrets.
- API and tests use env vars like `DATABASE_URL` (see `apps/api/pytest.ini`). Keep secrets in local env or vaults.

