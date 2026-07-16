.PHONY: test format migrate revision downgrade build-prod rmi-prod clean

test:
	python -m pip install -e .[dev]
	python run_tests.py

format:
	python -m black .

migrate:
	python -m alembic -c ironforgedcore/alembic.ini upgrade head

revision:
	python -m alembic -c ironforgedcore/alembic.ini revision --autogenerate -m "$(DESC)"

downgrade:
	python -m alembic -c ironforgedcore/alembic.ini downgrade -1

build-prod:
	python -m pip install --upgrade build
	python -m build

rmi-prod:
	rm -rf dist/ build/ *.egg-info

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"
