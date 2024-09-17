from io import StringIO
# pylint: disable-next=wildcard-import
from devdriven.rbac.rbac import \
  Resource, Action, Role, Group, RoleMembership, Identity, \
  Domain, Request, Solver, TextLoader
from devdriven.asserts import assert_output_by_key
# from icecream import ic

def test_rbac():
  def proc(actual_out):
    with open(actual_out, "w", encoding='utf-8') as out:
      def prt(x):
        print(x, file=out)
      run_test_rbac(prt)
  assert_output_by_key('run_test_rbac', 'tests/devdriven/output/rbac', proc)

# pylint: disable-next=too-many-statements
def run_test_rbac(prt):
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
    ]
  }

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
  loader = TextLoader(resource)
  rules = loader.read(io)

  domain = Domain(
    roles=[admin_role, read_role],
    rules=rules,
    role_memberships=role_memberships,
  )

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
