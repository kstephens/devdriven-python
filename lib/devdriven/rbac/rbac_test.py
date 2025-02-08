from pathlib import Path, PurePath
from ..asserts import assert_output_by_key
from . import Resource, Action, Request, Solver, TextLoader, DomainFileLoader
from .util import getter


def test_rbac_integration():
    run_test("test_rbac_integration", run_rbac_integration)


# pylint: disable-next=too-many-statements,too-many-locals
def run_rbac_integration(prt):
    base_dir = PurePath("tests/data/rbac")
    domain_base = base_dir / "domain"
    resource_root = base_dir / "root"
    domain = None

    def print_user(user):
        nonlocal domain
        groups = list(map(lambda o: o.name, user.groups))
        roles = list(map(lambda o: o.name, domain.roles_for_user(user)))
        prt(f"# identity {user.name}")
        prt(f"#   {groups=}")
        prt(f"#   {roles=}")

    with open(f"{domain_base}/user.txt", encoding="utf-8") as io:
        users = TextLoader("").read_users(io)
    with open(f"{domain_base}/role.txt", encoding="utf-8") as io:
        memberships = TextLoader("").read_memberships(io)
    with open(f"{domain_base}/password.txt", encoding="utf-8") as io:
        passwords = TextLoader("").read_passwords(io)
    roles = {}
    for member in memberships:
        roles[member.role.name] = member.role
    roles = roles.values()

    prt("")
    for user in users:
        prt(f"#  user {user.name} {','.join(map(getter('name'), user.groups))}")
    user_by_name = {user.name: user for user in users}
    for membership in memberships:
        prt(f"#  member {membership.role.name} {membership.member.name}")
    for role in roles:
        prt(f"#  role {role.name}")
    for password in passwords:
        prt(f"#  password {password.name} {password.password}")

    def fut(resource, action, user_name):
        nonlocal domain, roles, memberships

        user = user_by_name[user_name]
        request = Request(resource=Resource(resource), action=Action(action), user=user)

        domain = DomainFileLoader(
            user_file=Path(f"{domain_base}/user.txt"),
            membership_file=Path(f"{domain_base}/role.txt"),
            password_file=Path(f"{domain_base}/password.txt"),
            resource_root=resource_root,
            resource_path=Path(request.resource.name),
        ).domain()
        solver = Solver(domain=domain)
        rules = solver.find_rules(request)
        prt("")
        print_user(user)

        result = [rule.permission.name for rule in rules]
        result = [rule.brief() for rule in rules]
        result = ", ".join(result)

        given = f"fut({resource!r}, {action!r}, {user_name!r})"
        prt(f"assert {given:40s} == [{result}]")

    prt("\n# ############################################")

    prt("# =========================================")
    fut("/nope", "GET", "unknown")
    fut("/nope", "GET", "alice")
    fut("/nope", "GET", "root")

    prt("# =========================================")
    fut("/.hidden", "GET", "unknown")
    fut("/.hidden", "GET", "alice")
    fut("/a/.hidden", "GET", "unknown")
    fut("/a/.hidden", "GET", "alice")
    fut("/a/b/.hidden", "GET", "unknown")
    fut("/a/b/.hidden", "GET", "alice")

    prt("# =========================================")
    fut("/a/1", "GET", "unknown")
    fut("/a/1", "GET", "alice")
    fut("/a/1", "GET", "bob")
    fut("/a/1", "GET", "frank")
    fut("/a/1", "GET", "tim")

    prt("# =========================================")
    fut("/a/b/2", "GET", "unknown")
    fut("/a/b/2", "GET", "alice")
    fut("/a/b/2", "GET", "bob")
    fut("/a/b/2", "GET", "frank")
    fut("/a/b/2", "GET", "tim")

    prt("# =========================================")
    fut("/a/b/3", "PUT", "unknown")
    fut("/a/b/3", "PUT", "alice")
    fut("/a/b/3", "PUT", "bob")
    fut("/a/b/3", "PUT", "frank")
    fut("/a/b/3", "PUT", "tim")

    prt("# =========================================")
    fut("/a/b/c.txt", "PUT", "unknown")
    fut("/a/b/c.txt", "PUT", "alice")
    fut("/a/b/c.txt", "PUT", "bob")
    fut("/a/b/c.txt", "PUT", "frank")
    fut("/a/b/c.txt", "PUT", "tim")

    prt("# =========================================")
    fut("/.rbac.txt", "PUT", "unknown")
    fut("/.rbac.txt", "PUT", "alice")
    fut("/a/.rbac.txt", "PUT", "alice")
    fut("/a/b/.rbac.txt", "PUT", "alice")
    fut("/a/b/c/.rbac.txt", "PUT", "alice")


def run_test(name, test_fun):
    def proc(actual_out):
        with open(actual_out, "w", encoding="utf-8") as out:

            def prt(x):
                print(x, file=out)

            test_fun(prt)

    assert_output_by_key(name, "tests/devdriven/output/rbac", proc)
