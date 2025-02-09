from typing import Any, Iterable, Literal, Annotated, List, Dict, Tuple
import copy
from pathlib import Path
import re
import json
import logging
import sys
import os
from icecream import ic
from .loader import DomainLoader, DomainFileLoader  # TextLoader
from .auth import Authenticator, AuthBasic, AuthBearer, AuthCookie, AuthUserPass, Cookie, Auth
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

class App:
    def __init__(
        self, resource_root: str, domain_root: str, authenticator: Authenticator,
    ):
        self.resource_root = Path(resource_root)
        self.domain_root = Path(domain_root)
        self.authenticator = authenticator
        self.environ: Dict[str, str] = {}
        self.start_response = None
        self.domain_loader = None
        self.auth_cookie_name = "authsession"
        self.verbose = False

    def login(self, username: str, password: str) -> Tuple[bool, Cookie]:
        auth = self.authenticator.auth_user_pass(username, password)
        logging.info("%s", f"{username=} {password=} {auth=}")
        return True, (self.auth_cookie_name, username)

    def is_allowed(self, action: str, resource: str, username: str) -> Tuple[bool, Any]:
        rule: Rule = self.solve(action, resource, username)
        result = {
            "permission": rule.permission.name,
            "action": action,
            "resource": resource,
            "user": username,
            "rule": {
                "permission": rule.permission.name,
                "action": rule.action.name,
                "role": rule.role.name,
            },
        }
        return rule.permission.name == "allow", result

    def authenticate(self, auth: str | None, cookie: str | None) -> str:
        username = None
        if auth is not None:
            if result := self.authenticator.auth_header(auth):
                username = result[0]
        if cookie is not None:
            if result := self.authenticator.auth_cookie((self.auth_cookie_name, cookie)):
                username = result[0]
        if username is None:
            username = ""
        return username

    def resource_get(
        self,
        action: str,
        resource: str,
        auth_header: str | None,
        auth_cookie: str | None,
    ):
        path = Path(str(self.resource_root) + resource)
        status = body = None
        headers = {}
        if not os.access(str(path), os.R_OK):
            status = 404
        else:
            allowed, _result = self.check_access(action, resource, auth_header, auth_cookie)
            if not allowed:
                status = 401
        if not status:
            with open(path, "rb") as io:
                status = 200
                body = io.read()
                headers["Content-Type"] = 'application/binary'
        if not status:
            status = 403
        if not body:
            body = f"{status}\n".encode()
            headers["Content-Type"] = "text/plain"
        return status, headers, body

    def check_access(
        self,
        action: str,
        resource: str,
        auth_header: str | None,
        auth_cookie: str | None,
        ):
        # ic(auth_header)
        # ic(auth_cookie)
        username = self.authenticate(auth_header, auth_cookie)
        success, result = self.is_allowed(action, resource, username)
        return success, result

    def solve(self, action_name: str, resource_path: str, username: str) -> Rule:
        resource = Resource(resource_path)
        domain = self.make_domain(resource)
        solver = Solver(domain=domain)
        user = domain.user_for_name(username)
        request = Request(
            action=Action(action_name),
            resource=resource,
            user=user,
        )

        rules: Iterable = []
        if not (action_name and username and user):
            rules = [ self.default_rule(request) ]
        else:
            rules = solver.find_rules(request)

        if self.verbose:
            if isinstance(self.domain_loader, DomainFileLoader):
                logging.info(
                    "  files_loaded  : %s",
                    repr([str(p) for p in self.domain_loader.files_loaded]),
                )
            logging.info("  action        : %s", repr(request.action.name))
            logging.info("  resource      : %s", repr(request.resource.name))
            logging.info("  user          : %s", repr(request.user and request.user.name))
            logging.info(
                "  groups        : %s", repr(request.user and [g.name for g in request.user.groups])
            )
            logging.info(
                "  roles         : %s",
                repr(request.user and [r.name for r in domain.roles_for_user(request.user)]),
            )
            logging.info("  rules         : %s", len(list(rules)))
            for rule in rules:
                logging.info("                : %s", rule.brief())

        return next(iter(rules))

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
            user_file=self.domain_root / "user.txt",
            membership_file=self.domain_root / "role.txt",
            password_file=self.domain_root / "password.txt",
            resource_root=self.resource_root,
            resource_path=Path(resource.name),
        )
        domain = domain_loader.domain()
        self.domain_loader = domain_loader
        return domain


class UnsafeAuthenticator(Authenticator):
    def challenge_userpass(self, auth: AuthUserPass) -> Auth | None:
        ic(auth)
        return auth[1], auth

    def challenge_basic(self, auth: AuthBasic) -> Auth | None:
        ic(auth)
        return auth[1][0], auth

    def challenge_bearer(self, auth: AuthBearer) -> Auth | None:
        ic(auth)
        return auth[1], auth

    def challenge_cookie(self, auth: AuthCookie) -> Auth | None:
        ic(auth)
        return auth[1], auth
