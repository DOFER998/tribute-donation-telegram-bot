.PHONY: install lint format typecheck check test up down migrate revision run dev

install:
	uv sync

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

typecheck:
	uv run ty check

check: lint typecheck test

test:
	uv run pytest --cov=src --cov-report=term-missing

up:
	docker compose -f docker-compose.local.yml up -d

down:
	docker compose -f docker-compose.local.yml down

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(msg)"

run:
	uv run python -m src.main

dev: up
	uv run python -m src.main
