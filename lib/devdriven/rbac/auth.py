from typing import Tuple, Literal
from abc import ABC, abstractmethod
import re
import base64

Username = str
Password = str
UserPass = Tuple[Username, Password]
Token = str
CookieName = str
CookieValue = str
Cookie = Tuple[CookieName, CookieValue]
AuthUserPass = Tuple[Literal["UserPass"], UserPass]
AuthBasic = Tuple[Literal["Basic"], UserPass]
AuthBearer = Tuple[Literal["Bearer"], Token]
AuthCookie = Tuple[Literal["Cookie"], Cookie]
Auth = Tuple[Username, AuthUserPass | AuthBasic | AuthBearer | AuthCookie]


class Authenticator(ABC):
    @abstractmethod
    def challenge_userpass(self, auth: AuthUserPass) -> Auth | None:
        pass

    @abstractmethod
    def challenge_basic(self, auth: AuthBasic) -> Auth | None:
        pass

    @abstractmethod
    def challenge_bearer(self, auth: AuthBearer) -> Auth | None:
        pass

    @abstractmethod
    def challenge_cookie(self, auth: AuthCookie) -> Auth | None:
        pass

    ###################################################

    def auth_user_pass(self, username: Username, password: Password) -> Auth | None:
        return self.challenge_userpass(("UserPass", (username, password)))

    def auth_header(self, auth_header: str) -> Auth | None:
        if basic := self.parse_auth_basic(auth_header):
            return self.challenge_basic(basic)
        if bearer := self.parse_auth_bearer(auth_header):
            return self.challenge_bearer(bearer)
        return None

    def auth_cookie(self, cookie: Cookie) -> Auth | None:
        return self.challenge_cookie(("Cookie", cookie))

    ###################################################

    def parse_auth_basic(self, auth_header: str) -> AuthBasic | None:
        if m := re.match(r"^Basic +(\S+)$", auth_header):
            basic_auth = base64.b64decode(m[1]).decode()
            username, password = basic_auth.split(":", 1)
            return "Basic", (username, password)
        return None

    def parse_auth_bearer(self, auth_header: str) -> AuthBearer | None:
        if m := re.match(r"^Bearer +(\S+)$", auth_header):
            return "Bearer", m[1]
        return None

    def parse_cookie(self, cookie: Cookie) -> AuthCookie | None:
        if m := re.match(r'^(?P<cookie_name>[^=]+)="(?P<cookie_value>.*)"$', cookie):
            return "Cookie", (m["cookie_name"], m["cookie_value"])
        if m := re.match(r"^(?P<cookie_name>[^=]+)=(?P<cookie_value>.*)$", cookie):
            return "Cookie", (m["cookie_name"], m["cookie_value"])
        return None
