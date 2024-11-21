#!/usr/bin/env python3
from typing import Optional  # List, Iterable
import logging
import re
import base64
from operator import is_not
from functools import partial
import ldap  # type: ignore
# from icecream import ic

class LDAPService():
  config: dict

  def __init__(self, config: dict):
    self.config = config
    self.ldap_obj = None

  def connect(self):
    ldap_obj = ldap.initialize(self.config['url'])
    # pylint: disable-next=no-member
    ldap_obj.protocol_version = ldap.VERSION3
    if self.config['tlsrequirecert'] != 'true':
      # ??? \'TLS: hostname does not match CN in peer certificate\'}
      # pylint: disable-next=no-member
      ldap_obj.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, 0)
    if self.config['starttls'] == 'true':
      ldap_obj.start_tls_s()
    if self.config['disable_referrals'] == 'true':
      # pylint: disable-next=no-member
      ldap_obj.set_option(ldap.OPT_REFERRALS, 0)
    # pylint: disable-next=consider-using-f-string
    binddn = self.config['binddn'] % {'binduser': self.config['binduser']}
    # pylint: disable-next=no-member
    ldap_obj.bind_s(binddn, self.config['bindpasswd'], ldap.AUTH_SIMPLE)
    self.ldap_obj = ldap_obj

  def authenticate_user(self, req):
    res = req | {'status': 'unknown', 'exception': None}
    secret = res.pop('secret')
    try:
      user_info = res['user_info'] = self.get_user_info(req)
      if user_info['status'] == 'success':
        # pylint: disable-next=no-member
        self.ldap_obj.bind_s(user_info['dn'], secret, ldap.AUTH_SIMPLE)
        res['status'] = 'success'
    # pylint: disable-next=broad-except
    except Exception as exc:
      res['exception'] = repr(exc)
      return self.auth_failed(res, repr(exc))
    return res

  def encode_auth_token(self, req):
    token = '|'.join(['1', req['user'], req['secret']])
    token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
    return token

  def decode_auth_token(self, token):
    version, user, secret = base64.b64decode(token.encode('utf-8')).decode('utf-8').split('|')
    return {'version': version, 'user': user, 'secret': secret}

  # pylint: disable-next=too-many-locals
  def get_user_info(self, req):
    res = {'user': req['user'], 'status': 'unknown', 'exception': None}
    try:
      template = self.config.get('template') or '(sAMAccountName=%(username)s)'
      # pylint: disable-next=consider-using-f-string
      searchfilter = template % {'username': req['user']}
      # attributes = ['*']  # ['objectclass']
      # attributes = ['(objectClass=*)']
      # attributes = ['()']
      results = self.ldap_obj.search_s(
        self.config['basedn'],
        # pylint: disable-next=no-member
        ldap.SCOPE_SUBTREE,
        filterstr=searchfilter,
        # attrlist=attributes,
        attrsonly=0
      )
      nres = len(results)
      if nres < 1:
        return self.auth_failed(res, 'no objects found')
      if nres > 1:
        self.log_message("note: filter match multiple objects: {nres}, using first")
      user_entry = results[0]
      res['dn'], user_attributes = user_entry
      # ic(sorted(user_attributes.keys()))
      interesting_attributes = (
        'name',
        'givenName', 'distinguishedName', 'displayName',
        'sAMAccountName', 'sAMAccountType',
        'mail', 'mailNickname',
        'uid', 'uidNumber', 'gidNumber', 'primaryGroupID',
        'whenCreated',
      )
      attrs = res['attrs'] = {}
      for attr in interesting_attributes:
        attrs[attr] = [b.decode('utf-8') for b in user_attributes.get(attr, [])]
      member_of = user_attributes.get('memberOf', [])
      attrs['groups'] = sorted(list(filter(partial(is_not, None), map(parse_group_cn, member_of))))
      if not res['dn']:
        return self.auth_failed(res, 'no DN')
      res['status'] = 'success'
    # pylint: disable-next=broad-except
    except Exception as exc:
      res['exception'] = repr(exc)
      return self.auth_failed(res, repr(exc))
    return res

  def auth_failed(self, res, msg):
    res['status'] = 'failed'
    res['error'] = msg
    logging.error('auth_failed: %s', repr(res))
    return res

  def log_message(self, msg):
    logging.info('%s', msg)

def parse_group_cn(item: bytes) -> Optional[str]:
  if m := re.search(r'^CN=(?P<CN>[^,]+)(?:,|$)', item.decode(encoding='utf-8')):
    return m['CN']
  return None

# def slice(indexable, keys):
#   return {k: indexable[k] for k in keys if k in indexable}
