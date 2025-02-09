"""
To start:

PYTHONPATH=lib:$PYTHONPATH python -m devdriven.rbac.api

curl http://localhost:8888/__access/GET/a/f1.txt | jqm
curl http://bob@localhost:8888/__access/GET/a/f1.txt | jqm
curl http://bob:@localhost:8888/__access/GET/a/f1.txt | jqm
curl http://bob:b0b3r7@localhost:8888/a/f1.txt | jqm
curl http://bob:b0b3r7@localhost:8888/__access/GET/a/f1.txt | jqm
curl http://bob@localhost:8888/__access/GET/a/f1.txt
curl http://localhost:8888/__access/GET/a/f1.txt
curl http://bolocalhost:8888/a/f1.txt
curl http://bob:b0b3r7@localhost:8888/__access/GET/a/f1.txt
curl http://bob:b0b3r7@localhost:8888/__access/GET/a/f2.txt
curl http://bob:b0b3r7@localhost:8888/a/f2.txt
curl http://bob:b0b3r7@localhost:8888/a/f1.txt
curl --data-binary='abc' -X PUT http://bob:b0b3r7@localhost:8888/a/f9.txt
curl http://bob:b0b3r7@localhost:8888/a/f9.txt
curl --data-binary 'abc' -X PUT http://bob:b0b3r7@localhost:8888/a/f9.txt
curl --data-binary 'abc' -X PUT http://bob:b0b3r7@localhost:8888/a/b/bob.txt
curl --data-binary 'frank was here!' -X PUT http://frank:crick@localhost:8888/a/b/frank.txt

"""

from typing import Literal, Annotated, Callable
import re
import logging
import sys
import uvicorn
from fastapi import FastAPI, Cookie, Path, Form, Header, status
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from fastapi.requests import Request
from asgiref.sync import async_to_sync
from .app import App, ResourceRequest

####################################################

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


app = App(
    resource_root="tests/data/rbac/root",
    domain_root="tests/data/rbac/domain",
)

####################################################

UserName = Annotated[str, Path(pattern=re.compile(r"^[a-z][a-z0-9_]*$"))]

api = FastAPI()

ActionName = Literal["GET", "HEAD", "PUT", "DELETE"]
SessionCookie = Annotated[str | None, Cookie()]
AuthorizationHeader = Annotated[str | None, Header()]


@api.get("/")
def redirect_to_docs():
    return RedirectResponse("/docs", status_code=status.HTTP_303_SEE_OTHER)


@api.get("/__login")
def get_login():
    body = """
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


@api.post("/__login")
def post_login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    response: Response,
):
    cookie = app.login(username, password)
    logging.info("%s", f"{cookie=}")
    if cookie:
        response = HTMLResponse(content="OK", status_code=200)
        response.set_cookie(cookie.name, cookie.value)
    else:
        response = RedirectResponse("/__login", status_code=status.HTTP_303_SEE_OTHER)
    return response


######################################


@api.get("/__access/{action}/{resource:path}")
def check_get_access(action: ActionName, resource: str, request: Request):
    return resource_request(action, resource, request, app.check_access)


######################################


@api.get("/{resource:path}")
def get_resource(resource: str, request: Request):
    return resource_request("GET", resource, request, app.resource_get)


@api.head("/{resource:path}")
def head_resource(resource: str, request: Request):
    return resource_request("HEAD", resource, request, app.resource_head)


@api.put("/{resource:path}")
def put_resource(resource: str, request: Request):
    return resource_request(
        "PUT", resource, request, app.resource_put, async_to_sync(request.body)()
    )


def resource_request(
    action: ActionName,
    resource: str,
    request: Request,
    func: Callable,
    body: bytes = b"",
):
    auth_header = request.headers.get("Authorization")
    auth_cookie = request.cookies.get(app.auth_cookie_name)
    req = ResourceRequest(action, f"/{resource}", auth_header, auth_cookie, body)
    code, headers, body = func(req)
    return Response(content=body, headers=headers, status_code=code)


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
