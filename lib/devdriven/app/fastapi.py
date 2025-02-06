"""
fastapi helpers.
"""

import fastapi.encoders
from fastapi.encoders import jsonable_encoder as jsonable_encoder_orig


def enable_as_dict_encoder():
    orig = jsonable_encoder_orig

    def as_dict_encoder(*args, **kwargs):
        obj = args[0]
        if encode := getattr(obj, "as_dict", None):
            args = list(args)
            args[0] = encode()
        return orig(*args, **kwargs)

    fastapi.encoders.jsonable_encoder = as_dict_encoder


def disable_as_dict_encoder():
    fastapi.encoders.jsonable_encoder = jsonable_encoder_orig
