import base64
from typing import Any, Iterable
from cryptography.fernet import Fernet


class Cipher:
    def __init__(self, key: str):
        self.key = key
        self.key_padded = base64.b64encode(pad(key, 32))
        self.encoding = "utf-8"

    def encrypt(self, b: bytes) -> bytes:
        return Fernet(self.key_padded).encrypt(b)

    def decrypt(self, b: bytes) -> bytes:
        return Fernet(self.key_padded).decrypt(b)

    def encipher_token(self, data: Iterable) -> str:
        result: Any = data
        for enc, _ in self.coders():
            result = enc(result)
        return result

    def decipher_token(self, token: str) -> Iterable:
        result: Any = token
        for _, dec in reversed(self.coders()):
            result = dec(result)
        return result

    def coders(self):
        return (
            (basic_auth_encode, basic_auth_decode),
            # (encode_utf_8, decode_utf_8),
            (add_header, remove_header),
            # (encode_utf_8, decode_utf_8),
            # (base64.b64encode, base64.b64decode),
            (self.encrypt, self.decrypt),
            (base64.b64encode, base64.b64decode),
        )


def basic_auth_encode(x):
    return b":".join(map(lambda s: s.encode("latin1"), x))


def basic_auth_decode(x):
    return list(map(lambda b: b.decode("latin1"), x.split(b":")))


def add_header(x):
    # print(f{HEADER=}")
    return b"1\t" + x


def remove_header(x):
    header, *data = x.split(b"\t")
    assert header == b"1"
    return data[0]


def encode_utf_8(x):
    return x.encode("utf-8")


def decode_utf_8(x):
    return x.decode("utf-8")


HEADER = [b"1", b"Fernet"]


def pad(x: str, size):
    return (((x + " ").encode("utf-8")) * size)[:size]


if __name__ == "__main__":
    cipher = Cipher("secret-key")
    data_in = ("username", "password")
    print(f"{data_in=}")
    data_enc = cipher.encipher_token(data_in)
    print(f"{data_enc=}")
    data_out = cipher.decipher_token(data_enc)
    print(f"{data_out=}")
