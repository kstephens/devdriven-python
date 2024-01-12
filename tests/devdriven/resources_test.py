from devdriven.resource import Resources

def test_resources():
  resources = Resources(search_paths=['.', 'tests'])
  assert resources.find_all(['Makefile']) == ['Makefile']
  assert resources.find(['devdriven/resources_test.py']) == 'tests/devdriven/resources_test.py'
