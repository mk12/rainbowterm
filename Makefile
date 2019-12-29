PY := python3

SRC_DIR := rainbowterm
TEST_DIR := tests

.PHONY: all fmt lint tc test install

all: fmt lint tc test

fmt:
	$(PY) -m black .

lint:
	$(PY) -m flake8

tc:
	$(PY) -m mypy

test:
	$(PY) -m pytest

install:
	$(PY) -m pip install -r requirements.txt
