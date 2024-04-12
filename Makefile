PYTHON=python3.11
PYTHONPATH_OTHER:=../devdriven-python/lib
DIRS_OTHER:=../devdriven-python
include ../devdriven-python/Makefile.common

README.md: doc/README-*.md
	cat doc/README-*.md > README.md

doc/README-10-help.md: lib/psv/*
	psv help --markdown --verbose > tmp/README-10-help.md
	mv tmp/README-10-help.md $@
