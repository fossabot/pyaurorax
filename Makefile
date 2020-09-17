.PHONY: install update test test-dev clean publish

all:

poetry:
	python -m pip install poetry

install: poetry
	poetry install

update:
	python -m pip install --upgrade poetry
	poetry update

clean:
	@rm -rf pyaurorax.egg-info build dist

test:
	find . -type f -name '*.py' -exec sed -i -e "s/\r//g" {} \;
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --ignore=W391 --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	pytest

test-dev:
	@echo "Type-checking ...\n============================="
	-mypy aurorax
	@echo "\n\n"
	@echo "Linting ...\n============================="
	-pylint aurorax
	@echo "\n\n"
	@echo "Security analysis ...\n============================="
	-bandit -r aurorax
	@echo "\n\n"
	@echo "Test coverage ...\n============================="
	-coverage report

publish:
	${MAKE} test
	poetry build
	poetry publish
	${MAKE} clean
