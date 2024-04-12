from devdriven.resource import Resources

def test_resources():
  resources = Resources(search_paths=['.', 'lib', 'tests'])
  assert resources.find_all(['Makefile']) == ['Makefile']
  assert resources.find(['devdriven/resources_test.py']) == 'lib/devdriven/resources_test.py'
  assert resources.find(['devdriven/data/actual.txt']) == 'tests/devdriven/data/actual.txt'
