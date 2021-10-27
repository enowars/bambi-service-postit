.PHONY: all lint diff format

all: format

lint:
	python3 -m black --check src
	python3 -m flake8 src
	python3 -m mypy src

diff:
	python3 -m isort --diff src
	python3 -m black --diff src

format:
	python3 -m isort src
	python3 -m black src

