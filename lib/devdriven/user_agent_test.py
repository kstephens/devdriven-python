from io import StringIO
import os
import contextlib
from devdriven.user_agent import UserAgent
from devdriven.file_response import FileResponse

TEST_FILE = "tmp/user-agent-test.csv"


def test_file_put_201_create():
    with contextlib.suppress(FileNotFoundError):
        os.remove(TEST_FILE)
    response = file_fut("put", TEST_FILE, body=b"OK\n")
    assert response.status == 201
    assert response.data == b"201 Created\n"
    assert response.headers["Content-Type"] == "text/plain"
    assert response.headers["content-type"] == "text/plain"
    assert "ETag" in response.headers


def test_file_get_200_readable():
    response = file_fut("get", TEST_FILE, preload_content=False)
    assert response.status == 200
    assert response.read() == b"OK\n"
    assert response.data == b""
    assert response.headers["Content-Type"] == "text/csv"
    assert "ETag" in response.headers


def test_file_get_200_preload():
    response = file_fut("get", TEST_FILE)
    assert response.status == 200
    assert response.data == b"OK\n"
    assert response.headers["Content-Type"] == "text/csv"
    assert "ETag" in response.headers


def test_file_put_201_changed():
    response = file_fut("put", TEST_FILE, body=b"CHANGED\n")
    assert response.status == 201
    assert response.data == b"201 Created\n"
    assert response.headers["Content-Type"] == "text/plain"
    assert "ETag" in response.headers


def test_file_get_200_changed():
    response = file_fut("get", TEST_FILE)
    assert response.status == 200
    assert "ETag" in response.headers
    assert response.headers["Content-Type"] == "text/csv"
    assert response.data == b"CHANGED\n"


def test_file_get_403_unreadable():
    os.chmod(TEST_FILE, 0)
    response = file_fut("get", "/etc/sudoers")
    assert response.status == 403
    assert response.data == b"403 Forbidden\n"
    assert response.headers["Content-Type"] == "text/plain"
    assert "ETag" not in response.headers


def test_file_get_404_non_existent():
    with contextlib.suppress(FileNotFoundError):
        os.remove(TEST_FILE)
    response = file_fut("get", TEST_FILE)
    assert response.status == 404
    assert response.data == b"404 Not Found\n"
    assert response.headers["Content-Type"] == "text/plain"
    assert "ETag" not in response.headers


def test_file_get_403():
    response = file_fut("get", "/etc/sudoers")
    assert response.status == 403
    assert response.data == b"403 Forbidden\n"
    assert response.headers["Content-Type"] == "text/plain"
    assert "ETag" not in response.headers


def test_file_get_stdin():
    test_stdin = StringIO("STDIN\n")
    response = file_fut("get", "-", headers={"X-STDIN": test_stdin})
    assert response.status == 200
    assert response.data == b"STDIN\n"
    assert "Content-Type" not in response.headers
    assert "ETag" not in response.headers


def xtest_file_put_stdout():
    test_stdout = StringIO()
    response = file_fut("put", "-", headers={"X-STDOUT": test_stdout}, body=b"STDOUT\n")
    assert response.status == 201
    assert response.data == b"201 Created\n"
    assert response.headers["Content-Type"] == "text/plain"
    assert "ETag" not in response.headers
    assert test_stdout.getvalue() == "STDOUT\n"


def test_http_get_200():
    response = http_fut("get", "https://github.com/")
    assert response.status == 200
    assert len(response.data) >= 100
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
    assert "ETag" in response.headers


def test_http_get_200_read():
    response = http_fut("get", "https://github.com/", preload_content=False)
    assert response.status == 200
    assert len(response.read()) >= 100
    assert response.data == b""
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
    assert "ETag" in response.headers


def file_fut(method, url, headers=None, body=None, **kwargs):
    fun = FileResponse().request
    response = assert_response(fun, method, url, headers, body, **kwargs)
    # pprint(response)
    if url == "-":
        return response
    # assert int(response.headers['Content-Length']) == len(response._body)
    return http_fut(method, url, headers=headers, body=body, **kwargs)


def http_fut(method, url, headers=None, body=None, **kwargs):
    return assert_response(
        UserAgent().request, method, url, headers=headers, body=body, **kwargs
    )


def assert_response(fun, method, url, headers=None, body=None, **kwargs):
    # pprint((method, url, headers, body))
    response = fun(method, url, headers=headers, body=body, **kwargs)
    # ic((method, url))
    # ic(response)
    # ic(response.status)
    # ic(response.headers)
    if not 200 <= response.status <= 299:
        # ic(response.status)
        # ic(response.headers)
        assert "ETag" not in response.headers
        assert "X-Error" in response.headers
    return response
