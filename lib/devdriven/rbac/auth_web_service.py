from typing import Dict  # Any, Optional, Self, Callable, Iterable, List, Type, IO
import copy
from pathlib import Path
import json
import logging
import sys
from icecream import ic
from .loader import DomainFileLoader  # TextLoader
from ..rbac import (
    Solver,
    Request,
    Permission,
    Action,
    Resource,
    Rule,
    Role,
)

# https://www.toptal.com/python/pythons-wsgi-server-application-interface


class AuthWebService:
    def __init__(self, base: Path, root: Path):
        self.base = base
        self.resource_root = root
        self.environ: Dict[str, str] = {}
        self.start_response = None
        self.request_number = 0

    def __call__(self, environ, start_response):
        self.request_number += 1
        inst = copy.copy(self)
        inst.environ = environ
        inst.start_response = start_response
        return inst

    def __iter__(self):
        status, headers, body = self.process_request(self.environ)
        self.start_response(status, headers)
        yield body.encode()

    def process_request(self, env: dict):
        # env = {k: v for k, v in env.items() if k not in os.environ}
        # ic(list(sorted(env.keys())))
        # ic(env['HTTP_AUTHORIZATION'])
        action = env.get("HTTP_X_AUTH_ACTION", env.get("REQUEST_METHOD"))
        resource = env.get("HTTP_X_AUTH_RESOURCE", env.get("PATH_INFO"))
        user = env.get("HTTP_X_AUTH_USER", env.get("REMOTE_USER")) or "unknown"
        rule = self.solve(action, resource, user)
        result = {
            "permission": rule.permission.name,
            "action": action,
            "resource": resource,
            "user": user,
            "rule": str(rule),
        }
        if rule.permission.name == "allow":
            status = "200 OK"
        else:
            status = "403 Forbidden"
        body = f"""
{self.request_number}
{json.dumps(result, indent=2)}
"""
        return (
            status,
            [("Content-type", "text/plain")],
            body,
        )

    def solve(self, action_name: str, resource_path: str, user_name: str):
        domain_loader = DomainFileLoader()
        domain = domain_loader.load_all(
            self.base / "user.txt",
            self.base / "role.txt",
            self.resource_root,
            Path(resource_path),
        ).create_domain()

        request = Request(
            action=Action(action_name),
            resource=Resource(resource_path),
            user=domain.user_for_name(user_name),
        )

        solver = Solver(domain=domain)
        rules = solver.find_rules(request)

        logging.info(
            "  files_loaded  : %s", repr([str(p) for p in domain_loader.files_loaded])
        )
        logging.info("  action        : %s", repr(request.action.name))
        logging.info("  resource      : %s", repr(request.resource.name))
        logging.info("  user          : %s", repr(request.user.name))
        logging.info(
            "  groups        : %s", repr([g.name for g in request.user.groups])
        )
        logging.info(
            "  roles         : %s",
            repr([r.name for r in domain.roles_for_user(request.user)]),
        )
        logging.info("  rules         : %s", len(list(rules)))
        for rule in rules:
            logging.info("                  : %s", rule.brief())

        if rules:
            return next(iter(rules))
        return self.default_rule(request)

    def default_rule(self, request: Request):
        return Rule(
            permission=Permission("deny"),
            action=request.action,
            role=Role("*"),
            resource=request.resource,
            description="<<DEFAULT>>",
        )


def start_app(port=8080):
    # pylint: disable-next=import-outside-toplevel
    from wsgiref.simple_server import make_server

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    base = Path("tests/data/rbac")
    root = base / "root"

    app = AuthWebService(base=base, root=root)
    ic(app)

    httpd = make_server("", port, app)
    print(f"Serving on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    start_app()
