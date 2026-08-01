.PHONY: test format migrate revision downgrade update-deps build-prod rmi-prod clean

test:
	uv sync --extra dev
	uv run python run_tests.py

format:
	uv sync --extra dev
	uv run python -m black .

migrate:
	uv run python -m alembic -c ironforgedcore/alembic.ini upgrade head

revision:
	uv run python -m alembic -c ironforgedcore/alembic.ini revision --autogenerate -m "$(DESC)"

downgrade:
	uv run python -m alembic -c ironforgedcore/alembic.ini downgrade -1

update-deps:
	uv lock --upgrade

build-prod:
	uv run --with build python -m build

rmi-prod:
	rm -rf dist/ build/ *.egg-info

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"
