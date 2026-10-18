# Thin aliases over scripts/dev.py, which does the real work on Windows, macOS and Linux.
# Without make: `python scripts/dev.py <target>`. Extra args: `make test ARGS="-k store"`.

ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif
DEV = $(PYTHON) scripts/dev.py

.PHONY: help setup setup-ml server client tunnel test test-client e2e lint format types

help:
	@echo "setup | setup-ml | server | client | tunnel | test | test-client | e2e | lint | format | types"

setup:
	$(DEV) setup

setup-ml:
	$(DEV) setup-ml

server:
	$(DEV) server $(ARGS)

client:
	$(DEV) client $(ARGS)

tunnel:
	$(DEV) tunnel

test:
	$(DEV) test $(ARGS)

test-client:
	$(DEV) test-client

e2e:
	$(DEV) e2e $(ARGS)

lint:
	$(DEV) lint

format:
	$(DEV) format

types:
	$(DEV) types
