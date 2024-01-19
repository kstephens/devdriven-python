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

BIN_FILES:=$(shell grep -Erl '^\#!.+python' bin)
LIB_FILES:=$(shell find lib -name '*.py' | sort)
TEST_FILES:=$(shell find tests -name '*.py' | sort)
LINT_FILES:=$(BIN_FILES) $(LIB_FILES) $(TEST_FILES)
MYPY_FILES:=$(shell grep -Elr '^ *from typing import ' $(LINT_FILES))

default : all

all : venv check

# Environment:

venv: Makefile requirements.txt dev-requirements.txt
	$(MAKE) venv-create venv-upgrade-tools venv-install-requirements

venv-create:
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
	$(MAKE) install-requirements

venv-force:
	rm -rf venv/
	$(MAKE) venv

install-requirements:
	$(PYTHON) -m pip install -r requirements.txt -r dev-requirements.txt

# Check:

check: test lint mypy

run-check: run-test run-lint run-mypy

# Lint:

lint: pylint pycodestyle

pylint:
	$(MAKE) run-pylint FILES='$(or $(FILES), $(LINT_FILES))'

pycodestyle:
	$(MAKE) run-pycodestyle FILES='$(or $(FILES), $(LINT_FILES))'

mypy:
	$(MAKE) run-mypy FILES='$(or $(FILES), $(MYPY_FILES))'

run-lint: run-pylint run-pycodestyle

run-pylint:
	pylint --rcfile ./.pylintrc --recursive=y $(wildcard $(FILES))

run-pycodestyle:
	pycodestyle --config=.pycodestyle --show-source --statistics $(wildcard $(FILES))

MYPY_OPTS+= --config-file ./.mypy.ini
MYPY_OPTS+= # --strict
run-mypy:
	rm -rf mypy-report/
	mkdir -p mypy-report
	mypy $(MYPY_OPTS) --txt-report mypy-report $(wildcard $(or $(FILES), /dev/null))
	cat mypy-report/index.txt

# Unit Test:

test: unit-test

unit-test:
	$(MAKE) run-test FILES='$(or $(FILES), $(TEST_FILES))'

PYTEST_OPTS= #--capture=fd --show-capture
run-test:
	rm -rf coverage/
	mkdir -p coverage
	coverage run -m pytest $(PYTEST_OPTS) $(wildcard $(FILES)) -vv -rpP
	coverage report | tee coverage/coverage.txt
	coverage html
	coverage json
#	coverage xml

# Resources:

HTML_DIR=lib/devdriven/resources/html
JS_FILES:=$(shell find $(HTML_DIR)/*.js $(HTML_DIR)/vendor/tablesort-*/src -name '*.js' | grep -v '.min.js' | sort)
MIN_JS_FILES:=$(patsubst %.js,%.min.js,$(JS_FILES))

minify: $(MIN_JS_FILES) Makefile
%.min.js: %.js
	python -mrjsmin < $< > $@
	# slimit < $< > $@ # ModuleNotFoundError: No module named 'minifier'

minify-clean:
	rm -f $(MIN_JS_FILES)

# Productivity:

watch-files:
	tool/bin/watch-files

clean:
	rm -rf ./__pycache__ ./.pytest_cache ./.mypy_cache ./mypy-report ./htmlcov coverage/
	find lib tests -name '__pycache__' -a -type d | sort -r | xargs rm -rf {}
	rm -f $(MIN_JS_FILES)

very-clean: clean
	rm -rf ./venv

# Diagnostics:

env:
	. venv/bin/activate; env | sort

var:
	@echo '$($(v))'

vars:
	@$(foreach v,BIN_FILES LIB_FILES TEST_FILES LINT_FILES MYPY_FILES,echo '$(v)=$($(v))'; )
