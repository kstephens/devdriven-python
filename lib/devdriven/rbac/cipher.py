from typing import Any, Iterable
import base64
import hashlib
import hmac
import secrets
import random
import zlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


Data = str | bytes
Step = str
Steps = Iterable[Step]


class Cipher:
    def __init__(
        self,
        key: str,
        cipher_name: str = "",
        hash_name: str = "",
        frame_version: str = "",
    ):
        if not cipher_name:
            cipher_name = self.valid_cipher_names()[0]
        if not hash_name:
            hash_name = "sha1"
        if not frame_version:
            frame_version = "1"
        self.key, self.cipher_name, self.frame_version = key, cipher_name, frame_version
        self.hash_name = hash_name
        self.salt_length_range = range(0, 16)
        self.field_separator = b"\t"

    ###################################################
    # Hashing

    def hash(self, data: Data) -> Data:
        return self.coders_apply(self.hash_steps(), 0, data)

    def hmac(self, data: bytes) -> bytes:
        """Compute hash of arbitrary data."""
        frame = (
            str_encode(self.frame_version),
            b"hmac:" + str_encode(self.hash_name),
            str_encode(str(len(data))),
            data,
        )
        return hmac.digest(
            str_encode(self.key),
            self.fields_encode(frame),
            getattr(hashlib, self.hash_name),
        )

    def hash_steps(self) -> Steps:
        return ("str_encode", "hmac", "base64", "str_decode")

    ###################################################
    # Encipher/Decipher

    def encipher(self, data: Data) -> Data:
        """Encipher arbitrary data."""
        return self.coders_apply(self.cipher_steps(), 0, data)

    def decipher(self, data: Data) -> Data:
        """Decipher data enciphered above."""
        return self.coders_apply(self.cipher_steps(), 1, data)

    def cipher_steps(self) -> Steps:
        return (
            "str_encode",
            "check_bytes",
            "checksum",
            "frame",
            "cipher",
            "base64",
            "str_decode",
        )

    ###################################################

    def coders_apply(self, steps: Iterable[str], direction: int, data: Data) -> Data:
        if direction == 1:
            steps = reversed(tuple(steps))
        coders = self.coders()
        value: Any = data
        for step in steps:
            value = coders[step][direction](value)
        return value

    def coders(self):
        return {
            "str_encode": (str_encode, str_decode),
            "check_bytes": (is_bytes, is_bytes),
            "hmac": (self.hmac, identity),
            "checksum": (self.checksum_encode, self.checksum_decode),
            "frame": (self.frame_encode, self.frame_decode),
            "cipher": (self.cipher_encode, self.cipher_decode),
            "base64": (base64.b64encode, base64.b64decode),
            "str_decode": (str_decode, str_encode),
        }

    ###################################################
    # Framing

    def frame_encode(self, data: bytes) -> bytes:
        """
        Frame data as fields:
        - frame version
        - cipher name
        - data length
        - data salted with random bytes at the end
        The only supported frame version is "1"
        """
        self.check_frame_version(self.frame_version)
        salt_length = random.randint(
            self.salt_length_range.start, self.salt_length_range.stop
        )
        salted_data = data + secrets.token_bytes(salt_length)
        return self.fields_encode(
            (
                str_encode(self.frame_version),
                str_encode(self.cipher_name),
                str_encode(str(len(data))),
                salted_data,
            )
        )

    def frame_decode(self, data: bytes) -> bytes:
        record = self.fields_decode(data, 3)
        frame_version = str_decode(record[0])
        self.check_frame_version(frame_version)
        cipher_name, data_length, salted_data = (
            str_decode(record[1]),
            int(str_decode(record[2])),
            record[3],
        )
        salted_data_len = len(salted_data)
        self.check_cipher_name(cipher_name)
        if data_length < 0:
            raise ValueError("Cipher: {data_length=} < 0")
        if salted_data_len < data_length:
            raise ValueError("Cipher: {salted_data_len=} < {data_length=}")
        self.frame_version = frame_version
        self.cipher_name = cipher_name
        return salted_data[:data_length]

    def check_frame_version(self, frame_version: str):
        if frame_version != "1":
            raise ValueError("Cipher: invalid {frame_version=}")

    def fields_encode(self, datums: tuple) -> bytes:
        return self.field_separator.join(datums)

    def fields_decode(self, data: bytes, n: int) -> tuple:
        return tuple(data.split(self.field_separator, n))

    ###################################################

    def checksum_encode(self, payload: bytes) -> bytes:
        return self.fields_encode((self.checksum(payload), payload))

    def checksum_decode(self, data: bytes) -> bytes:
        crc, payload = self.fields_decode(data, 1)
        if crc != self.checksum(payload):
            raise ValueError("Cipher: invalid checksum")
        return payload

    def checksum(self, data: bytes) -> bytes:
        self.check_frame_version(self.frame_version)
        crc32 = zlib.crc32(data) & 0xFFFFFFFF
        return str_encode(f"crc32:{crc32:08x}")

    ###################################################

    def cipher_encode(self, data: bytes) -> bytes:
        """
        Encipher data.
        Pad self.key as needed.
        Add nonce if needed.
        """
        if self.cipher_name == "AESGCM-256":
            # https://stackoverflow.com/a/59835994/1141958
            # AESGCM key must be 128, 192, or 256 bits.
            # GCM mode needs 12 nonce bytes:
            nonce = secrets.token_bytes(12)
            return nonce + AESGCM(self.key_padded(256)).encrypt(nonce, data, b"")
        if self.cipher_name == "Fernet":
            # Fernet key must be 256 bits.
            return Fernet(self.key_padded(256)).encrypt(data)
        self.check_cipher_name(self.cipher_name)
        return b""

    def cipher_decode(self, data: bytes) -> bytes:
        """
        Decipher data.
        Pad self.key as needed.
        """
        if self.cipher_name == "AESGCM-256":
            return AESGCM(self.key_padded(256)).decrypt(data[:12], data[12:], b"")
        if self.cipher_name == "Fernet":
            return Fernet(self.key_padded(256)).decrypt(data)
        self.check_cipher_name(self.cipher_name)
        return b""

    def key_padded(self, n_bits: int) -> bytes:
        """
        Repeat self.key to fill n_bits.
        Fill with zero if self.key is blank.
        """
        assert n_bits % 8 == 0
        n_bytes: int = n_bits // 8
        self.check_frame_version(self.frame_version)
        key = str_encode(self.key)
        if not key:
            return b"\0" * n_bytes
        if len(key) < n_bytes:
            key += key * n_bytes
        return key[:n_bytes]

    def check_cipher_name(self, cipher_name: str) -> str:
        if cipher_name not in self.valid_cipher_names():
            raise ValueError(f"Cipher: invalid cipher {cipher_name!r}")
        return cipher_name

    def valid_cipher_names(self) -> tuple:
        return ("AESGCM-256", "Fernet")


def identity(x):
    return x


def str_encode(x: Data) -> bytes:
    if isinstance(x, bytes):
        return x
    return x.encode("utf-8")


def str_decode(x: Data) -> str:
    if isinstance(x, str):
        return x
    return x.decode("utf-8")


def is_bytes(x):
    if not isinstance(x, bytes):
        raise TypeError("expected bytes: given {type(x)!r}")
    return x
