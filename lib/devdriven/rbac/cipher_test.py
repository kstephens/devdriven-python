from . import cipher as sut


def test_round_trip():
    cipher = sut.Cipher("secret-key")
    data_in = ["username", "password"]
    data_enc = cipher.encipher_token(data_in)
    print(f"data_enc = {data_enc!r}")
    data_out = cipher.decipher_token(data_enc)
    assert data_out == data_in
