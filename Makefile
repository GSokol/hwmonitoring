PYTHON ?= python3

test:
	$(PYTHON) -m pytest -vv tests/
