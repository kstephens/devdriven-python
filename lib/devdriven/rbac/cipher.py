from typing import Any, Iterable
import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class Cipher:
    def __init__(self, key: str, cipher: str = "AESGCM", format: str = "1"):
        self.key, self.cipher, self.format = key, cipher, format
        self.token_format_bytes = bytes(str(self.format).encode())
        self.encoding = "utf-8"

    def encipher(self, data: Iterable[str]) -> str:
        value: Any = data
        for enc, _ in self.coders():
            print(f"encipher: {value=}")
            value = enc(value)
        print(f"encipher: {value=} : DONE")
        return value

    def decipher(self, token: str) -> Iterable[str]:
        value: Any = token
        for _, dec in reversed(self.coders()):
            print(f"decipher: {value=}")
            value = dec(value)
        print(f"decipher: {value=} : DONE")
        return value

    # Fernet key must be 256
    # AESGCM key must be 128, 192, or 256 bits.
    def encipher_bytes(self, b: bytes) -> bytes:
        key_padded = pad_key(self.key, 256 // 8)
        if self.cipher == "Fernet":
            return Fernet(key_padded).encrypt(b)
        if self.cipher == "AESGCM":
            # https://stackoverflow.com/a/59835994/1141958
            # GCM mode needs 12 nonce bytes:
            nonce = secrets.token_bytes(12)
            return nonce + AESGCM(key_padded).encrypt(nonce, b, b"")
        raise ValueError("unknown cipher {self.cypher!r}")

    def decipher_bytes(self, b: bytes) -> bytes:
        key_padded = pad_key(self.key, 256 // 8)
        if self.cipher == "Fernet":
            return Fernet(key_padded).decrypt(b)
        if self.cipher == "AESGCM":
            return AESGCM(key_padded).decrypt(b[:12], b[12:], b"")
        raise ValueError("unknown cipher {self.cypher!r}")

    def coders(self):
        return (
            (basic_auth_encode, basic_auth_decode),
            # (encode_utf_8, decode_utf_8),
            (self.add_header, self.remove_header),
            # (encode_utf_8, decode_utf_8),
            # (base64.b64encode, base64.b64decode),
            (self.encipher_bytes, self.decipher_bytes),
            (base64.b64encode, base64.b64decode),
        )

    def add_header(self, data: bytes) -> bytes:
        print(f"add_header data = {bytes(data)!r}")
        record = [to_bytes(self.format), to_bytes(self.cipher), data]
        return b"\t".join(record)

    def remove_header(self, record: bytes):
        format, cipher, *data = record.split(b"\t")
        assert to_str(format) == self.format
        assert to_str(cipher) == self.cipher
        return data[0]


def to_bytes(x: str) -> bytes:
    return bytes(x.encode("latin1"))


def to_str(x: bytes) -> str:
    return x.decode("latin1")


def basic_auth_encode(strs: Iterable[str]) -> bytes:
    return b":".join([to_bytes(s) for s in strs])


def basic_auth_decode(x: bytes) -> Iterable[str]:
    return [to_str(b) for b in x.split(b":")]


def encode_utf_8(x):
    return x.encode("utf-8")


def decode_utf_8(x):
    return x.decode("utf-8")


def pad_key(key: str, n_bytes: int) -> bytes:
    return ((key.encode("utf-8") + b"\0") * n_bytes)[:n_bytes]


if __name__ == "__main__":
    cipher = Cipher("secret-key")
    data_in = ("username", "password")
    print(f"{data_in=}")
    data_enc = cipher.encipher(data_in)
    print(f"{data_enc=}")
    data_out = cipher.decipher(data_enc)
    print(f"{data_out=}")
