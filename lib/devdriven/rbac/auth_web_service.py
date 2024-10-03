# from typing import Any, Optional, Self, Callable, Iterable, List, Type, IO
import copy
from pathlib import Path
import json
import logging
import sys
# import os
from icecream import ic
from devdriven.rbac import Solver, \
  Request, Permission, Action, Resource, Rule, Role, \
  DomainFileLoader

# https://www.toptal.com/python/pythons-wsgi-server-application-interface

class AuthWebService:
  def __init__(self, base, root):
    self.base = base
    self.resource_root = root
    self.environ = {}
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

  def process_request(self, env):
    # env = {k: v for k, v in env.items() if k not in os.environ}
    # ic(list(sorted(env.keys())))
    # ic(env['HTTP_AUTHORIZATION'])
    action = env.get('HTTP_X_AUTH_ACTION', env.get('REQUEST_METHOD'))
    resource = env.get('HTTP_X_AUTH_RESOURCE', env.get('PATH_INFO'))
    user = env.get('HTTP_X_AUTH_USER', env.get('REMOTE_USER')) or 'unknown'
    rule = self.solve(action, resource, user)
    result = {
      'action': action,
      'resource': resource,
      'user': user,
      'rule': str(rule),
    }
    body = f"""
{self.request_number}
{json.dumps(result, indent=2)}
"""
    return (
      '200 OK',
      [('Content-type', 'text/plain')],
      body,
    )

  def solve(self, action_name: str, resource_name: str, user_name: str):
    action = Action(action_name)
    resource = Resource(resource_name)
    domain_loader = DomainFileLoader(
      users_file=self.base / "user.txt",
      memberships_file=self.base / "role.txt",
      resource_root=self.resource_root,
      resource=Path(resource.name)
    )
    domain = domain_loader.load_domain()
    user = domain.user_for_name(user_name)
    request = Request(resource=resource, action=action, user=user)
    logging.info("  files_loaded  : %s", repr(domain_loader.files_loaded))
    logging.info("  user          : %s", repr(user))
    logging.info("  groups        : %s", repr(user.groups))
    logging.info("  roles         : %s", repr(domain.roles_for_user(user)))
    logging.info("  resource      : %s", repr(resource))
    solver = Solver(domain=domain)
    rules = solver.find_rules(request)
    if rules:
      return rules[0]
    return self.default_rule(request)

  def default_rule(self, request):
    return Rule(
      permission=Permission('deny'),
      action=request.action,
      role=Role('*'),
      resource=request.resource,
      description='<<DEFAULT>>'
    )


def start_app(port=8080):
  # pylint: disable-next=import-outside-toplevel
  from wsgiref.simple_server import make_server
  logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
  base = Path('tests/data/rbac')
  root = base / 'root'

  app = AuthWebService(base=base, root=root)
  ic(app)

  httpd = make_server('', port, app)
  print(f'Serving on port {port}...')
  httpd.serve_forever()


if __name__ == '__main__':
  start_app()
