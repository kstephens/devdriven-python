from . import cipher as sut


def test_cipher():
    cipher = sut.Cipher("secret-key", cipher_name="AESGCM-256")
    data_in = "username\tpassword"
    data_enc_1 = cipher.encipher(data_in)
    # print(f"{data_enc_1=}")
    assert isinstance(data_enc_1, str)
    assert len(data_enc_1) >= 72
    # print(f"{len(data_enc_1)=} bytes : {data_enc_1=}")

    data_out = cipher.decipher(data_enc_1)
    # print(f"{data_out=}")
    assert data_out == data_in, "expected round-trip"

    data_enc_2 = cipher.encipher(data_in)
    # print(f"{data_enc_2=}")
    assert data_enc_2 != data_enc_1, "expected salting difference"
