from . import cipher as sut


def test_round_trip():
    cipher = sut.Cipher("secret-key")
    data_in = ["username", "password"]
    data_enc = cipher.encipher(data_in)
    # print(f"{data_enc=}")
    data_out = cipher.decipher(data_enc)
    # print(f"{data_out=}")
    assert data_out == data_in
