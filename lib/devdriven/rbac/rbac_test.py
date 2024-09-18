from io import StringIO
from pathlib import Path, PurePath
from devdriven.rbac.rbac import \
  Resource, Action, Role, Group, RoleMembership, Identity, \
  Domain, Request, Solver, IdentityRoles, \
  TextLoader, FileSystemLoader
from devdriven.rbac.rbac import clean_path

from devdriven.asserts import assert_output_by_key
# from icecream import ic

def test_clean_path():
  assert clean_path('.a') == '.a'
  assert clean_path('/.a') == '/.a'
  assert clean_path('.') == '.'
  assert clean_path('./') == ''  # ???
  assert clean_path('..') == ''
  assert clean_path('../') == ''  # ???
  assert clean_path('/..') == '/'
  assert clean_path('/../a') == '/a'
  assert clean_path('a') == 'a'
  assert clean_path('/a') == '/a'
  assert clean_path('//a') == '/a'
  assert clean_path('//a//') == '/a/'
  assert clean_path('dir//a//') == 'dir/a/'
  assert clean_path('/root//a//') == '/root/a/'
  assert clean_path('dir/../a/b') == 'a/b'
  assert clean_path('/root/../b') == '/b'
  assert clean_path('dir/a/../b') == 'dir/b'
  assert clean_path('dir/a/../../b/c') == 'b/c'

def test_file_system_loader():
  run_test('test_file_system_loader', run_file_system_loader)

# pylint: disable-next=too-many-statements
def run_file_system_loader(prt):
  root = PurePath('/root')
  files = {
    '/root/.auth.txt': '''
allow *   admin  **/.auth.txt
allow *   admin  **
allow *   admin  **/.*
deny  *   *      **/.auth.txt
deny  *   anon   **
    ''',
    '/root/a/.auth.txt': '''
allow GET other    *
allow PUT a-writer writable.txt
    ''',
    '/root/a/b/.auth.txt': '''
allow GET read  *
allow PUT write *.txt
    ''',
    '/root/a/b/c/.auth.txt': None,
  }

  def open_file(path):
    if file := files[str(path)]:
      return StringIO(file)
    return None
  domain, identity_by_name = make_domain([])

  def print_identity(identity):
    groups = list(map(lambda o: o.name, identity.groups))
    roles = list(map(lambda o: o.name, IdentityRoles(domain).identity_roles(identity)))
    prt(f"# identity {identity.name}")
    prt(f"#   groups = {groups!r}")
    prt(f"#   roles = {roles!r}")

  def fut(resource, action, ident):
    nonlocal domain
    identity = identity_by_name[ident]

    request = Request(resource=Resource(resource), action=Action(action), identity=identity)

    loader = FileSystemLoader(root=root, open_file=open_file)
    rules_for_resource = loader.load_rules(Path(request.resource.name))

    prt("")
    print_identity(identity)
    prt(f"\n# rules for {resource!r}:")
    prt('\n'.join([f"# {rule.brief()}" for rule in rules_for_resource]))
    domain.rules = rules_for_resource
    solver = Solver(domain=domain)
    rules = solver.find_rules(request)

    result = [rule.permission.name for rule in rules]
    result = [rule.brief() for rule in rules]
    result = ', '.join(result)

    prt(f"assert fut({resource!r}, {action!r}), {ident!r} == [{result}]")

  prt("\n# ############################################")
  for identity in identity_by_name.values():
    print_identity(identity)

  prt('# =========================================')
  fut('/nope', 'GET', 'unknown')
  fut('/nope', 'GET', 'alice')

  prt('# =========================================')
  fut('/a/1', 'GET', 'unknown')
  fut('/a/1', 'GET', 'alice')
  fut('/a/1', 'GET', 'bob')
  fut('/a/1', 'GET', 'frank')
  fut('/a/1', 'GET', 'tim')

  prt('# =========================================')
  fut('/a/b/2', 'GET', 'unknown')
  fut('/a/b/2', 'GET', 'alice')
  fut('/a/b/2', 'GET', 'bob')
  fut('/a/b/2', 'GET', 'frank')
  fut('/a/b/2', 'GET', 'tim')

  prt('# =========================================')
  fut('/a/b/3', 'PUT', 'unknown')
  fut('/a/b/3', 'PUT', 'alice')
  fut('/a/b/3', 'PUT', 'bob')
  fut('/a/b/3', 'PUT', 'frank')
  fut('/a/b/3', 'PUT', 'tim')

  prt('# =========================================')
  fut('/a/b/c.txt', 'PUT', 'unknown')
  fut('/a/b/c.txt', 'PUT', 'alice')
  fut('/a/b/c.txt', 'PUT', 'bob')
  fut('/a/b/c.txt', 'PUT', 'frank')
  fut('/a/b/c.txt', 'PUT', 'tim')

  prt('# =========================================')
  fut('/.auth.txt', 'PUT', 'unknown')
  fut('/.auth.txt', 'PUT', 'alice')
  fut('/a/.auth.txt', 'PUT', 'alice')
  fut('/a/b/.auth.txt', 'PUT', 'alice')
  fut('/a/b/c/.auth.txt', 'PUT', 'alice')

def test_text_loader():
  run_test('test_loader', run_test_text_loader)

# pylint: disable-next=too-many-statements
def run_test_text_loader(prt):
  text = '''
  # a comment

allow *   admin  *
allow *   admin  .*
allow GET *      README.*
allow GET read   *.c
allow PUT write  *
deny  *   *      *

  '''
  io = StringIO(text)
  resource = Resource('/a')
  loader = TextLoader(resource.name)
  rules = loader.read(io)
  domain, identity_by_name = make_domain(rules)
  solver = Solver(domain=domain)

  def fut(resource, action, identity):
    ident = identity_by_name[identity]
    request = Request(resource=Resource(resource), action=Action(action), identity=ident)
    rules = solver.find_rules(request)
    result = [rule.permission.name for rule in rules]
    prt(f"assert fut({resource!r}, {action!r}), {identity!r} == {result!r}")

  prt(text)
  fut('/nope', 'GET', 'unknown')
  fut('/nope', 'GET', 'alice')

  fut('/a/b', 'GET', 'unknown')
  fut('/a/b', 'GET', 'alice')
  fut('/a/b', 'GET', 'bob')
  fut('/a/b', 'GET', 'frank')

  fut('/a/b.c', 'GET', 'unknown')
  fut('/a/b.c', 'PUT', 'unknown')
  fut('/a/b.c', 'GET', 'alice')
  fut('/a/b.c', 'PUT', 'alice')
  fut('/a/b.c', 'GET', 'bob')
  fut('/a/b.c', 'PUT', 'bob')
  fut('/a/b.c', 'GET', 'frank')
  fut('/a/b.c', 'PUT', 'frank')

  fut('/a/.c', 'GET', 'unknown')
  fut('/a/.c', 'GET', 'alice')
  fut('/a/.c', 'GET', 'bob')
  fut('/a/.c', 'GET', 'frank')

  fut('/a/README.md', 'GET', 'unknown')
  fut('/a/README.md', 'PUT', 'unknown')
  fut('/a/README.md', 'GET', 'alice')
  fut('/a/README.md', 'PUT', 'alice')
  fut('/a/README.md', 'GET', 'bob')
  fut('/a/README.md', 'PUT', 'bob')
  fut('/a/README.md', 'GET', 'frank')
  fut('/a/README.md', 'PUT', 'frank')

# pylint: disable-next=too-many-statements
def make_domain(rules):
  # pylint: disable=too-many-locals
  admin_role = Role('admin')
  read_role = Role('read')
  write_role = Role('write')
  other_role = Role('other')
  anon_role = Role('anon')

  admin_group = Group('admins')
  readers_group = Group('readers')
  writers_group = Group('writers')
  other_group = Group('other')
  anon_group = Group('anon')

  role_memberships = [
    RoleMembership(role=role, member=member) for role, member in [
      (admin_role, admin_group),
      (read_role, readers_group),
      (write_role, writers_group),
      (other_role, other_group),
      (anon_role, anon_group),
    ]
  ]
  identity_by_name = {
    id.name: id for id in [
      Identity('unknown', groups=[anon_group]),
      Identity('alice', groups=[admin_group]),
      Identity('bob', groups=[readers_group]),
      Identity('frank', groups=[writers_group, other_group]),
      Identity('tim', groups=[other_group]),
    ]
  }
  domain = Domain(
    roles=[admin_role, read_role],
    rules=rules,
    role_memberships=role_memberships,
  )
  return domain, identity_by_name

def run_test(name, test_fun):
  def proc(actual_out):
    with open(actual_out, "w", encoding='utf-8') as out:
      def prt(x):
        print(x, file=out)
      test_fun(prt)
  assert_output_by_key(name, 'tests/devdriven/output/rbac', proc)

def getter(name: str):  # -> Callable:
  return lambda obj: getattr(obj, name)()
