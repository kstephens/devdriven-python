PYTHON=python3.11
OTHER_PYTHONPATH=../devdriven-python/lib
OTHER_DIRS=../devdriven-python
include ../devdriven-python/Makefile.common

check:
	@set -xe; for dir in $(OTHER_DIRS); do $(MAKE) -C "$$dir" $@; done
