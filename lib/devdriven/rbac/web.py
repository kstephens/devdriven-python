#!/usr/bin/env python3
from typing import Any, Callable, Dict  # List, Iterable
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
    password: str | None
    token: str | None
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
        token = env.get("X-Authorization")
        token = token or parse_bearer_token(env["Authorization"])
        return AuthRequest(
            method=env.get("X-Action") or env["REQUEST_METHOD"],
            resource=env.get("X-Resource") or env["PATH_INFO"],
            user=env.get("X-User"),
            password=env.get("X-Pass"),
            token=token,
            env=env,
        )


def parse_bearer_token(auth: str) -> str | None:
    if m := re.match(r"^\s*Bearer\s*(\S*)\s*$", auth):
        return m[1]
    return None


def application(env, start_response):
    env_json = json.dumps(list(dict(env).keys()), indent=2)
    logging.info("%s", f"env=\n{env_json}")
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello World\n", env_json.encode()]


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
