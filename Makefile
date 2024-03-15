PYTHON=python3.11
OTHER_PYTHONPATH=../devdriven-python/lib
OTHER_DIRS=../devdriven-python
include ../devdriven-python/Makefile.common

README.md: doc/README-*.md
	cat doc/README-*.md > README.md

doc/README-10-help.md:
	$(MAKE) check
	psv example --generate
	psv help --markdown --verbose > tmp/README-10-help.md
	mv tmp/README-10-help.md $@
