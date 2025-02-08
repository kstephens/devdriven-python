"""
To start:
PYTHONPATH=lib:$PYTHONPATH python -m devdriven.rbac.auth_web_service

curl http://localhost:8080/a/x
curl http://bob@localhost:8080/a/x
curl -H 'Authorization: Bearer bob' http://localhost:8080/a/x
curl -H 'Cookie: SESSIONID=bob' http://localhost:8080/a/x
curl http://asdfasdf@localhost:8080/a/x

"""

from typing import Self, Dict, Tuple, List
import copy
from pathlib import Path
import json
import logging
import sys
import os
from icecream import ic
from .loader import DomainLoader, DomainFileLoader  # TextLoader
from .auth import Authenticator, AuthBasic, AuthBearer, AuthCookie, Auth
from ..rbac import (
    Domain,
    Solver,
    Request,
    Permission,
    Action,
    Resource,
    Rule,
    Role,
)

# https://www.toptal.com/python/pythons-wsgi-server-application-interface


AuthResponse = Tuple[str, List[Tuple[str, str]], str]


class AuthWebService:
    domain_loader: DomainLoader | None

    def __init__(
        self, resource_root: Path, config_root: Path, authenticator: Authenticator
    ):
        self.resource_root = resource_root
        self.config_root = config_root
        self.authenticator = authenticator
        self.environ: Dict[str, str] = {}
        self.start_response = None
        self.request_number = 0
        self.domain_loader = None

    def __call__(self, environ, start_response) -> Self:
        self.request_number += 1
        inst = copy.copy(self)
        inst.environ = environ
        inst.start_response = start_response
        self.domain_loader = None
        return inst

    def __iter__(self):
        status, headers, body = self.process_request(self.environ)
        self.start_response(status, headers)
        yield body.encode()

    def process_request(self, env: dict) -> AuthResponse:
        env = {k: v for k, v in env.items() if k not in os.environ}
        ic(list(sorted(env.keys())))
        action = env.get("HTTP_X_AUTH_ACTION", env.get("REQUEST_METHOD"))
        resource = env.get("HTTP_X_AUTH_RESOURCE", env.get("PATH_INFO"))
        username = self.authenticate(env)
        ic(username)
        rule = self.solve(action, resource, username)
        result = {
            "request_id": self.request_number,
            "permission": rule.permission.name,
            "action": action,
            "resource": resource,
            "user": username,
            "rule": str(rule),
        }
        if rule.permission.name == "allow":
            status = "200 OK"
        else:
            status = "403 Forbidden"
        body = f"""
{json.dumps(result, indent=2)}
"""
        return (
            status,
            [("Content-type", "text/plain")],
            body,
        )

    def authenticate(self, env: dict) -> str:
        username = None
        header = env.get("HTTP_X_AUTHORIZATION", env.get("HTTP_AUTHORIZATION"))
        if header:
            if auth := self.authenticator.auth_header(header):
                username = auth[0]
        header = env.get("HTTP_X_COOKIE", env.get("HTTP_COOKIE"))
        if header:
            if auth := self.authenticator.auth_cookie(header):
                username = auth[0]
        if username is None:
            username = ""
        return username

    def solve(self, action_name: str, resource_path: str, user_name: str) -> Rule:
        resource = Resource(resource_path)
        domain = self.make_domain(resource)
        solver = Solver(domain=domain)
        user = domain.user_for_name(user_name)
        request = Request(
            action=Action(action_name),
            resource=resource,
            user=user,
        )

        if not (action_name and user_name and user):
            return self.default_rule(request)
        rules = solver.find_rules(request)

        if isinstance(self.domain_loader, DomainFileLoader):
            logging.info(
                "  files_loaded  : %s",
                repr([str(p) for p in self.domain_loader.files_loaded]),
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

    ##########################################################

    def default_rule(self, request: Request) -> Rule:
        return Rule(
            permission=Permission("deny"),
            action=request.action,
            role=Role("*"),
            resource=request.resource,
            description="<<DEFAULT>>",
        )

    ##########################################################

    # This can be overriden to use a different domain loader.
    def make_domain(self, resource: Resource) -> Domain:
        domain_loader = DomainFileLoader(
            user_file=self.config_root / "user.txt",
            membership_file=self.config_root / "role.txt",
            password_file=self.config_root / "password.txt",
            resource_root=self.resource_root,
            resource_path=Path(resource.name),
        )
        domain = domain_loader.domain()
        self.domain_loader = domain_loader
        return domain


class UnsafeAuthenticator(Authenticator):
    def challenge_basic(self, auth: AuthBasic) -> Auth | None:
        return auth[1], auth

    def challenge_bearer(self, auth: AuthBearer) -> Auth | None:
        return auth[1], auth

    def challenge_cookie(self, auth: AuthCookie) -> Auth | None:
        if auth[1] != "SESSIONID":
            return None
        return auth[2], auth


def start_app(
    root="tests/data/rbac/root", config_dir="tests/data/rbac/domain", port=8080
):
    # pylint: disable-next=import-outside-toplevel
    from wsgiref.simple_server import make_server

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    authenticator = UnsafeAuthenticator()
    app = AuthWebService(
        resource_root=Path(root),
        config_root=Path(config_dir),
        authenticator=authenticator,
    )
    ic(app)

    httpd = make_server("", port, app)
    print(f"Serving on port {port}...")
    httpd.serve_forever()


if __name__ == "__main__":
    start_app()
