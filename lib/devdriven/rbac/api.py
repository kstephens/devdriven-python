'''
To start:

PYTHONPATH=lib:$PYTHONPATH python -m devdriven.rbac.api

curl http://localhost:8080/a/x
curl http://bob@localhost:8080/a/x
curl -H 'Authorization: Bearer bob' http://localhost:8080/a/x
curl -H 'Cookie: SESSIONID=bob' http://localhost:8080/a/x
curl http://asdfasdf@localhost:8080/a/x

'''
from typing import Literal, Annotated, List, Dict, Tuple
import re
import logging
import sys
from .app import App, UnsafeAuthenticator
from icecream import ic
import uvicorn
import fastapi
from fastapi import FastAPI, HTTPException, Cookie, Path, Form, Header, status
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from fastapi.requests import Request

####################################################

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


app = App(
    resource_root="tests/data/rbac/root",
    domain_root="tests/data/rbac/domain",
    authenticator=UnsafeAuthenticator(),
)

####################################################

UserName = Annotated[str, Path(pattern=re.compile(r"^[a-z][a-z0-9_]*$"))]

api = FastAPI()

ActionName = Literal["GET", "PUT", "POST", "DELETE"]
SessionCookie = Annotated[str | None, Cookie()]
AuthorizationHeader = Annotated[str | None, Header()]

@api.get('/')
def redirect_to_docs():
    return RedirectResponse('/docs', status_code=status.HTTP_303_SEE_OTHER)

@api.get('/__login')
def get_login(
        response_class=HTMLResponse
    ):
    body = f"""
<html>
<head>
</head>
<body>
  <form method="post">
    <div>
    <label for="username">Username:</label><br>
    <input type="text" id="username" name="username"><br>
    </div>
    <div>
    <label for="password">Password:</label><br>
    <input type="password" id="password" name="password">
    </div>
    <div>
      <input type="submit" id="submit" />
    </div>
  </form>
</body>
</html>
    """
    return HTMLResponse(content=body, status_code=200)

@api.post('/__login')
def post_login(
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        response: Response,
    ):
    success, cookie = app.login(username, password)
    logging.info("%s", f"{success=} {cookie=}")
    if success:
        response = HTMLResponse(content="OK", status_code=200)
        response.set_cookie(cookie[0], cookie[1])
    else:
        response = RedirectResponse('/__login', status_code=status.HTTP_303_SEE_OTHER)
    return response

@api.get('/__access/{action}/{resource:path}')
def check_get_access(
    action: ActionName,
    resource: str,
    request: Request,
    response: Response,
    ):
    auth_header = request.headers.get("Authorization")
    auth_cookie = request.cookies.get(app.auth_cookie_name)
    success, result = app.check_access(action, f"/{resource}", auth_header, auth_cookie)
    if success:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
    return result

@api.get('/{resource:path}')
def get_resource(
    resource: str,
    request: Request,
    ):
    auth_header = request.headers.get("Authorization")
    auth_cookie = request.cookies.get(app.auth_cookie_name)
    status, headers, body = app.resource_get("GET", f"/{resource}", auth_header, auth_cookie)
    response = Response(content=body, headers=headers, status_code=status)
    return response

######################################

if __name__ == "__main__":
    uvicorn.run(
        "devdriven.rbac.api:api",
        host="0.0.0.0",
        port=8888,
        reload=True,
        reload_dirs=["lib"],
        reload_excludes=["*_test.py"],
    )
