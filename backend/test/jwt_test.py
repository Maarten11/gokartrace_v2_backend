from auth import encode_token, decode_token

def jwt_test():
    original = {"foo": "bar"}

    token, expires = encode_token(original)

    result = decode_token(token)

    assert(result == original)