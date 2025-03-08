#!/usr/bin/env python3
import logging
import re
import sys
from pprint import pprint
from operator import is_not
from functools import partial
import urllib.parse
import ssl
import ldap3  # type: ignore
from .cipher import Cipher

# from icecream import ic


class LDAPService:
    config: dict

    def __init__(self, config: dict):
        self.config = config
        self.conn = None

    def connect(self):
        # ???: cleanup option names:
        url = urllib.parse.urlparse(self.config["url"])
        host = url.hostname
        tls = ldap3.Tls(
            validate=(
                ssl.CERT_REQUIRED
                if self.config["ssl_cert_required"]
                else ssl.CERT_OPTIONAL
            ),
        )
        server = ldap3.Server(
            host=host,
            use_ssl=self.config["ssl"],
            tls=tls,
        )
        conn = ldap3.Connection(
            server,
            user=self.config["bind_user"],
            password=self.config["bind_password"],
            version=3,
            auto_referrals=self.config["referrals"],
            read_only=True,
        )
        self.conn = conn

    def authenticate_user(self, req):
        res = req | {"status": "unknown", "exception": None}
        secret = res.pop("secret")
        try:
            user_info = res["user_info"] = self.get_user_info(req)
            if user_info["status"] == "success":
                # pylint: disable-next=no-member
                self.conn.bind_s(user_info["dn"], secret, ldap3.SIMPLE)
                res["status"] = "success"
        # pylint: disable-next=broad-except
        except Exception as exc:
            res["exception"] = repr(exc)
            return self.auth_failed(res, repr(exc))
        return res

    def encode_auth_token(self, req):
        return Cipher(self.auth_token_key()).encipher((req["user"], req["secret"]))

    def decode_auth_token(self, token):
        user, secret = Cipher(self.auth_token_key()).decipher(token)
        return {"user": user, "secret": secret}

    def auth_token_key(self) -> str:
        return self.config.get("auth_key", "")

    # pylint: disable-next=too-many-locals
    def get_user_info(self, req):
        res = {"user": req["user"], "status": "unknown", "exception": None}
        try:
            template = self.config.get("template") or "(sAMAccountName=%(username)s)"
            # pylint: disable-next=consider-using-f-string
            search_filter = template % {"username": req["user"]}
            # attributes = ['*']  # ['objectclass']
            # attributes = ['(objectClass=*)']
            # attributes = ['()']
            results = self.conn.search(
                search_base=self.config["base_dn"],
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                dereference_aliases=ldap3.DEREF_SEARCH,
                attributes=ldap3.ALL_OPERATIONAL_ATTRIBUTES,
            )
            nres = len(results)
            if nres < 1:
                return self.auth_failed(res, "no objects found")
            if nres > 1:
                self.log_message(
                    "note: filter match multiple objects: {nres}, using first"
                )
            user_entry = results[0]
            res["dn"], raw_attributes = user_entry["dn"], user_entry["raw_attributes"]
            # ic(sorted(user_attributes.keys()))
            interesting_attributes = (
                "name",
                "givenName",
                "distinguishedName",
                "displayName",
                "sAMAccountName",
                "sAMAccountType",
                "mail",
                "mailNickname",
                "uid",
                "uidNumber",
                "gidNumber",
                "primaryGroupID",
                "whenCreated",
            )
            attrs = res["attrs"] = {}
            for attr in interesting_attributes:
                attrs[attr] = [b.decode("utf-8") for b in raw_attributes.get(attr, [])]
            member_of = raw_attributes.get("memberOf", [])
            attrs["groups"] = sorted(
                list(filter(partial(is_not, None), map(parse_group_cn, member_of)))
            )
            if not res["dn"]:
                return self.auth_failed(res, "no DN")
            res["status"] = "success"
        # pylint: disable-next=broad-except
        except Exception as exc:
            res["exception"] = repr(exc)
            return self.auth_failed(res, repr(exc))
        return res

    def auth_failed(self, res, msg):
        res["status"] = "failed"
        res["error"] = msg
        logging.error("auth_failed: %s", repr(res))
        return res

    def log_message(self, msg):
        logging.info("%s", msg)


def parse_group_cn(item: bytes) -> str | None:
    if m := re.search(r"^CN=(?P<CN>[^,]+)(?:,|$)", item.decode(encoding="utf-8")):
        return m["CN"]
    return None


# def slice(indexable, keys):
#   return {k: indexable[k] for k in keys if k in indexable}


def main(argv):
    url, _method, *args = argv[1:]
    config = {
        "url": url,
        "bind_user": None,
        "bind_password": None,
        "ssl": True,
        "ssl_cert_required": False,
        "referrals": True,
        "base_dn": "ou=Accounts,dc=US,dc=test,dc=com",
    }
    svc = LDAPService(config)
    svc.connect()
    pprint(svc.get_user_info({"user": args[0]}))


if __name__ == "__main__":
    main(sys.argv)
