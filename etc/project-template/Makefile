ifndef VERBOSE
MAKEFLAGS += --no-print-directory
endif
base_dir:=$(shell readlink -f .)

PYTHONPATH_ORIG:=$(PYTHONPATH)
export PYTHONPATH=lib:$(PYTHONPATH_ORIG)
PYTHON=python3.11
PYTHON_BIN:=$(shell which $(PYTHON) | head -1)
VENV_OPTS=--clear
# OSX HAS WRECKED brew python3.*:
#VENV_OPTS+=--copies

BIN_FILES=$(shell grep -Erl '^\#!.+python' bin)
LIB_FILES=$(wildcard lib/**/*.py)
TEST_FILES=$(wildcard tests/**/*.py)
LINT_FILES=$(BIN_FILES) $(LIB_FILES) $(TEST_FILES)
MYPY_FILES=$(shell grep -Elr '^ *from typing import ' $(LINT_FILES))

default : all

all : venv check

# Environment:

venv: venv/bin/$(PYTHON) venv-upgrade-tools venv-install-requirements
venv-create: venv/bin/$(PYTHON)
venv/bin/$(PYTHON):
	which $(PYTHON) ;\
	env | grep -E 'LD_|PATH' ;\
	$(PYTHON) --version
	$(PYTHON_BIN) -m venv $(VENV_OPTS) ./venv
	. venv/bin/activate ;\
	env | grep -E 'LD_|PATH' ;\
	which $(PYTHON) ;\
	$(PYTHON) --version
# pip+3.10: SO MANY BUGS...
# https://stackoverflow.com/questions/72439001/there-was-an-error-checking-the-latest-version-of-pip
venv-upgrade-tools:
	- set -x ;\
	$(PYTHON) -m pip install --upgrade pip ;\
	. venv/bin/activate ;\
	pip install --upgrade pip ;\
	pip install --upgrade setuptools ;\
	pip install --upgrade distlib ;\
	$(MAKE) venv-install-requirements

venv-install-requirements: requirements.txt dev-requirements.txt
	. venv/bin/activate ;\
	$(PYTHON) -m pip install -r requirements.txt -r dev-requirements.txt

venv-force:
	rm -rf venv/
	$(MAKE) venv

check: test lint mypy

# Lint:

lint: pylint pycodestyle

pylint:
	pylint --rcfile ./.pylintrc --recursive=y $(LINT_FILES)

pycodestyle:
	pycodestyle --config=.pycodestyle --show-source --statistics $(LINT_FILES)

mypy:
	mkdir -p mypy-report
	mypy --config-file ./.mypy.ini --strict --txt-report mypy-report $(or $(MYPY_FILES), /dev/null)
	cat mypy-report/index.txt

# Unit Test:

test: run-tests

TESTS=
PYTEST_OPTS=
# PYTEST_OPTS=--capture=fd --show-capture
run-tests:
	rm -rf coverage/*
	coverage run -m pytest $(PYTEST_OPTS) all $(TESTS) -vv -rpP
	coverage report | tee coverage/coverage.txt
	coverage html
	coverage json
#	coverage xml

# Productivity:

watch-files:
	tool/bin/watch-files

clean:
	rm -rf ./__pycache__ ./.pytest_cache ./.mypy_cache ./mypy-report ./htmlcov coverage/.coverage coverage/*.*
	find lib tests -name '__pycache__' -a -type d | xargs rm -rf {}

very-clean: clean
	rm -rf ./venv

# Diagnostics:

env:
	. venv/bin/activate; env | sort

vars:
	@$(foreach v,BIN_FILES LIB_FILES TEST_FILES LINT_FILES MYPY_FILES,echo '$(v)=$($(v))'; )
