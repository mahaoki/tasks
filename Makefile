.PHONY: lint typecheck test

lint:
	pre-commit run --all-files

typecheck:
	mypy .

test:
	pytest --cov --cov-report=term-missing
