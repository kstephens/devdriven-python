PYTHON=python3.11
RESOURCES_DIR=lib/devdriven/resources
JS_FILES:=$(shell find $(RESOURCES_DIR)/js $(RESOURCES_DIR)/vendor/tablesort-*/src -name '*.js' | grep -v '.min.js' | sort)
include Makefile.common
