import re
import subprocess
import pytest
import devdriven.mime as sut

def test_guess_type():
  fut = sut.guess_type
  assert fut("a") == (None, None)
  assert fut("a.c") == ('text/x-c', None)
  assert fut("a.o") ==  ('application/octet-stream', None)
  assert fut("a.md") == ('text/markdown', None)
  assert fut("a.markdown") == ('text/markdown', None)

def test_short_and_long_suffix():
  fut = sut.short_and_long_suffix
  assert fut("a") == ('', '')
  assert fut("a.c") == ('.c', '.c')
  assert fut("a.tar.gz") ==  ('.gz', '.tar.gz')
  assert fut("a.b/c.d.e") == ('.e', '.d.e')

def test_content_type_for_suffixes():
  fut = sut.content_type_for_suffixes
  assert fut([".xls", ".xlst"]) == ('application/vnd.ms-excel', None)
  assert fut([".x", ".xbar"], ("DONT", "KNOW")) == ('DONT', 'KNOW')
