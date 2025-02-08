from . import cipher as sut


def test_cipher():
    cipher = sut.Cipher("secret-key", cipher_name="AESGCM-256")
    data_1 = "username\tpassword"
    data_enc_1 = cipher.encipher(data_1)
    data_dec_1 = cipher.decipher(data_enc_1)
    data_enc_2 = cipher.encipher(data_1)
    # print(f"{data_1=}")
    # print(f"{data_enc_1=}")
    # print(f"{len(data_enc_1)=} bytes : {data_enc_1=}")
    # print(f"{data_dec_1=}")
    # print(f"{data_enc_2=}")
    assert isinstance(data_enc_1, str)
    assert len(data_enc_1) >= 72
    assert data_dec_1 == data_1, "expected round-trip"
    assert data_enc_2 != data_enc_1, "expected salting difference"


def test_hash():
    cipher = sut.Cipher("secret-key")
    data_1 = "username\tpassword"
    data_2 = "username\tpassword-other"
    data_hash_1 = cipher.hash(data_1)
    data_hash_2 = cipher.hash(data_1)
    data_hash_3 = cipher.hash(data_2)
    cipher = sut.Cipher("secret-key-2")
    data_hash_4 = cipher.hash(data_1)
    # print(f"{data_1=}")
    # print(f"{data_2=}")
    # print(f"{data_hash_1=}")
    # print(f"{data_hash_2=}")
    # print(f"{data_hash_3=}")
    # print(f"{data_hash_4=}")
    assert isinstance(data_hash_1, str)
    assert data_hash_2 == data_hash_1
    assert data_hash_3 != data_hash_1
    assert data_hash_4 != data_hash_1
