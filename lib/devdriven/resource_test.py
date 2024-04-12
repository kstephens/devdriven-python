from devdriven.resource import Resources

def test_resources():
  resources = Resources(search_paths=['.', 'lib', 'tests'])
  assert resources.find_all(['Makefile']) == ['Makefile']
  assert resources.find(['devdriven/resource_test.py']) == 'lib/devdriven/resource_test.py'
  assert resources.find(['devdriven/data/actual.txt']) == 'tests/devdriven/data/actual.txt'
