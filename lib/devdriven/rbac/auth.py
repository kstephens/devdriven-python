from typing import cast
import logging
import re
import base64
from .cipher import Cipher
from .identity import Token, UserPass, Cookie
from .domain import IdentityDomain, PasswordDomain

Auth = UserPass | Token | Cookie


class Authenticator:
    identity_domain: IdentityDomain
    password_domain: PasswordDomain
    cipher_key: str
    cookie_name: str

    def __init__(
        self,
        identity_domain: IdentityDomain,
        password_domain: PasswordDomain,
        cipher_key: str,
        cookie_name: str,
    ):
        self.identity_domain, self.password_domain = identity_domain, password_domain
        self.cipher_key, self.cookie_name = cipher_key, cookie_name

    def authenticate(
        self,
        userpass: UserPass | None,
        auth: str | None,
        cookie: str | None,
    ) -> UserPass | None:
        result = None
        if userpass is not None and not result:
            result = self.auth_userpass(userpass)

        if auth is not None and not result:
            userpass = self.parse_basic(auth)
            if userpass is not None:
                return self.auth_userpass(userpass)
            if not result:
                token = self.parse_bearer(auth)
                if token is not None:
                    return self.auth_token(token)

        if cookie is not None and not result:
            result = self.auth_cookie(Cookie(self.cookie_name, cookie))
        return result

    def auth_userpass(self, userpass: UserPass) -> UserPass | None:
        """Verify username and password."""
        logging.debug("%s", f"auth_userpass: {userpass.username=}")
        if not (user := self.identity_domain.user_by_name(userpass.username)):
            return None
        logging.debug("%s", f"auth_userpass: {user=}")
        if not (password := self.password_domain.password_for_user(user)):
            return None
        matches = (
            password.username == userpass.username
            and password.password == userpass.password
        )
        logging.debug("%s", f"auth_userpass: {password.username=} {matches=}")
        if matches:
            return userpass
        return None

    def auth_cookie(self, cookie: Cookie) -> UserPass | None:
        return self.secret_to_userpass(cookie.value)

    def auth_token(self, token: Token) -> UserPass | None:
        return self.secret_to_userpass(token.value)

    ###################################################

    def userpass_cookie(self, userpass: UserPass) -> Cookie:
        return Cookie(self.cookie_name, self.userpass_to_secret(userpass))

    def userpass_token(self, userpass: UserPass) -> Token:
        return Token(self.userpass_to_secret(userpass))

    ###################################################

    def userpass_to_secret(self, userpass: UserPass) -> str:
        logging.debug("%s", f"userpass_to_secret: {userpass.username=}")
        cipher = Cipher(self.cipher_key)
        plaintext = f"{userpass.username}:{userpass.password}"
        return cast(str, cipher.encipher(plaintext))

    def secret_to_userpass(self, secret: str) -> UserPass:
        logging.info("%s", f"secret_to_userpass: {secret=}")
        cipher = Cipher(self.cipher_key)
        secret = cast(str, cipher.decipher(secret))
        username, password = secret.split(":", 1)
        return UserPass(username, password)

    ###################################################

    def parse_basic(self, auth_header: str) -> UserPass | None:
        if m := re.match(r"^Basic +(\S+)$", auth_header):
            basic_auth = base64.b64decode(m[1]).decode()
            username, password = basic_auth.split(":", 1)
            logging.debug("%s", f"parse_basic: {username=}")
            return UserPass(username, password)
        return None

    def parse_bearer(self, auth_header: str) -> Token | None:
        if m := re.match(r"^Bearer +(\S+)$", auth_header):
            token = m[1]
            logging.debug("%s", f"parse_bearer {token=}")
            return Token(token)
        return None
