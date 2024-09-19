from io import StringIO
from pathlib import Path, PurePath
from devdriven.rbac.rbac import \
  Resource, Action, \
  Domain, Request, Solver, UserRoles, \
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
    '/root/.user.txt': '''
user unknown  Anon
user alice    Admins
user bob      Readers
user frank    Writers,Other
user tim      Other
    ''',
    '/root/.role.txt': '''
member admin-role  Admins
member read-role   Readers
member write-role  Writers
member other-role  Other
member anon-role   Anon
    ''',
    '/root/.auth.txt': '''
perm allow *   admin-role  **/.user.txt
perm allow *   admin-role  **/.role.txt
perm allow *   admin-role  **/.auth.txt
perm allow *   admin-role  **
perm allow *   admin-role  **/.*
perm deny  *   *           **/.user.txt
perm deny  *   *           **/.role.txt
perm deny  *   *           **/.auth.txt
perm deny  *   anon-role   **
    ''',
    '/root/a/.auth.txt': '''
perm allow GET other-role    *
perm allow PUT a-writer-role writable.txt
    ''',
    '/root/a/b/.auth.txt': '''
perm allow GET read-role  *
perm allow PUT write-role *.txt
    ''',
    '/root/a/b/c/.auth.txt': None,
  }

  def open_file(path):
    if content := files[str(path)]:
      return StringIO(content)
    return None

  domain = None

  def print_user(user):
    nonlocal domain
    groups = list(map(lambda o: o.name, user.groups))
    roles = list(map(lambda o: o.name, UserRoles(domain).user_roles(user)))
    prt(f"# identity {user.name}")
    prt(f"#   groups = {groups!r}")
    prt(f"#   roles = {roles!r}")

  users = TextLoader('').read_users(open_file(root / '.user.txt'))
  memberships = TextLoader('').read_memberships(open_file(root / '.role.txt'))
  roles = [member.role for member in memberships]

  prt("")
  for user in users:
    prt(f"#  user {user.name} {','.join(map(getter('name'), user.groups))}")
  user_by_name = {user.name: user for user in users}
  for membership in memberships:
    prt(f"#  member {membership.role.name} {membership.member.name}")
  for role in roles:
    prt(f"#  role {role.name}")

  def fut(resource, action, user_name):
    nonlocal domain, roles, memberships

    user = user_by_name[user_name]
    request = Request(resource=Resource(resource), action=Action(action), user=user)

    loader = FileSystemLoader(root=root, open_file=open_file)
    rules_for_resource = loader.load_rules(Path(request.resource.name))

    prt("")
    domain = Domain(roles=roles, memberships=memberships, rules=rules_for_resource)
    solver = Solver(domain=domain)
    rules = solver.find_rules(request)
    print_user(user)
    # prt(f"\n# rules for {resource!r}:")
    # prt('\n'.join([f"# {rule.brief()}" for rule in rules_for_resource]))

    result = [rule.permission.name for rule in rules]
    result = [rule.brief() for rule in rules]
    result = ', '.join(result)

    prt(f"assert fut({resource!r}, {action!r}), {user_name!r} == [{result}]")

  prt("\n# ############################################")

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

def run_test(name, test_fun):
  def proc(actual_out):
    with open(actual_out, "w", encoding='utf-8') as out:
      def prt(x):
        print(x, file=out)
      test_fun(prt)
  assert_output_by_key(name, 'tests/devdriven/output/rbac', proc)

def getter(name: str):  # -> Callable:
  return lambda obj: getattr(obj, name)
