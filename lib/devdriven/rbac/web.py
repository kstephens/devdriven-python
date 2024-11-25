#!/usr/bin/env python3
from typing import Any, Optional, Callable, Dict  # List, Iterable
import logging
import json
import sys

# import os
import re

# import base64
from dataclasses import dataclass  # , field

# from operator import is_not
# from functools import partial
from .rbac import Permission  # ,Request

# from icecream import ic


@dataclass
class AuthRequest:
    method: str
    resource: str
    user: str
    password: Optional[str]
    token: Optional[str]
    env: Dict[str, Any]


@dataclass
class AuthResponse:
    permission: Permission
    status: str
    headers: Dict[str, str]


Authenticator = Callable[[AuthRequest], AuthResponse]


@dataclass
class WebAuthService:
    authenticator: Authenticator

    def application(self, env, start_response):
        req = self.make_auth_request(env)
        res = self.authenticator(req)
        start_response(str(res.status), [res.headers])
        return [res.body]

    def make_auth_request(self, env):
        return AuthRequest(
            method=env.get("X-Action") or env["REQUEST_METHOD"],
            resource=env.get("X-Resource") or env["PATH_INFO"],
            user=env.get("X-User"),
            password=env.get("X-Pass"),
            token=env.get("X-Authorization")
            or parse_bearer_token(env["Authorization"]),
            env=env,
        )


def parse_bearer_token(auth: str) -> Optional[str]:
    if m := re.match(r"^\s*Bearer\s*(\S*)\s*$", auth):
        return m[1]
    return None


def application(env, start_response):
    env_json = json.dumps(list(dict(env).keys()), indent=2)
    logging.info("%s", f"env=\n{env_json}")
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello World\n", env_json.encode()]


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
