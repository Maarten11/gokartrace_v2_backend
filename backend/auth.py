from flask_restful import Resource
from flask import request, make_response, Response
from jwt import encode, decode, ExpiredSignatureError
from os import environ
from enum import IntEnum
import time
import bcrypt

from sqlalchemy import select
from models import User, engine, sessions


ALGORITHM = "HS256"
ISSUER="GoKartRaceAPI"
KEY = environ["key"]
TOKEN_VALID_TIME = 300 # Time in seconds

class TokenState(IntEnum):
    """
    Enum for Token States
    """
    VALID = 1
    EXPIRED = 2
    INVALID = 3


def encode_token(content: dict) -> tuple[str, int]:
    """Encodes content into a jwt token

    :param content: Content to encode
    :return: JWT Token
    """
    now = int(time.time())
    expires = now + TOKEN_VALID_TIME
    h = {"exp": expires, "iat": now, "iss": ISSUER, "content": content}
    return encode(h, KEY, algorithm=ALGORITHM), expires


def decode_token(token: str) -> tuple[TokenState,dict]:
    """Decode jwt token to get content

    :param token: Token to decode
    :return: tuple containing token state and contents (if succesfull)
    """
    try:
        content = decode(token, KEY, algorithms=[ALGORITHM], issuer=ISSUER, options={"require": ["exp", "iat", "iss"]})
        return TokenState.VALID, content["content"]
    except ExpiredSignatureError as error:
        return TokenState.EXPIRED, error.__repr__()
    except Exception as error:
        return TokenState.INVALID, error.__repr__()


# def check_password(username: str, password: str) -> bool:
#     """Check if user and password combination exists

#     :param username: username
#     :param password: password
#     :return: True if combination exists
#     """
#     with sessions() as session:
#         result = session.execute(select(User.password).where(User.username == username)).scalar_one_or_none()
#         print(result, type(result), "Result", flush=True)

#         if result is None:

#         session.commit()

#         return bcrypt.checkpw(password, result)



class Login(Resource):
    def route():
        return "/login"

    def post(self) -> Response:
        if not request.form:
            return make_response("Form expected but not found", 400)

        # Extract info from request
        form_data = request.form

        if "username" not in form_data.keys() or not form_data["username"]:
            return make_response("Please provide username in form", 400)
        if "password" not in form_data.keys() or not form_data["password"]:
            return make_response("Please provide password in form", 400)

        user = form_data["username"]
        password = form_data["password"]
        # FIXME Not finished

        print(user, password, flush=True)

        # Fetch and check password
        with sessions() as session:
            # Fetch user object from database matching username
            result = session.execute(select(User).where(User.username == user)).scalar_one_or_none()
            session.commit()
            print(result, type(result), "Result", flush=True)

            # No user found -> error
            if result is None:
                return make_response(f"User {user} does not exist", 400)

            # Check password -> error if mismatched
            if not bcrypt.checkpw(password.encode(), result.password):
                return make_response("User or password incorrect", 401)

            # Generate token
            token, expires = encode_token({"user_id": result.id})

            # Make response with cookie
            resp = make_response("Logged in", 200)
            resp.set_cookie("jwt", token, expires=expires, samesite="Lax", secure=False, httponly=False)
            # resp.set_cookie("jwt", token, expires=expires, samesite="None", secure=True, httponly=True, domain="gokartrace.ask-stuwer.be")
            return resp



        result = check_password(user, password)
        print(result, flush=True)
        # # Check database for match
        # with sessions() as session:
        #     print("I am here", flush=True)
        #     result = session.execute(select(User)\
        #         .where(and_(User.password == password, User.username == user)))\
        #         .scal()
        #     print("I am here again", flush=True)
        #     print(result, type(result), flush=True)

        if result is None:
            return make_response("User or password incorrect", 401)

        print(result, type(result), flush=True)

        # Encode user_id in token so that intercepted cookies do not disclose any user names
        token, expires = encode_token({"user_id": result.id})

        resp = make_response("Logged in", 200)
        resp.set_cookie("jwt", token, expires=expires)
        return resp

def auth_valid(func):
    """Wrapper for routes that require authentication
    Use by putting `@auth_valid` above your route

    :param func: Function to wrap

    :note : The wrapped function needs a
    """
    def check_auth(*args, **kwargs):
        # XXX: REMOVE THIS LINE BEFORE PRODUCTION
        # return func(*args, **kwargs)

        # Check if cookie present
        if 'jwt' not in request.cookies:
            response = make_response("Could not find jwt authentication", 401)
            return response

        # Cookie is present
        jwt_token = request.cookies['jwt']

        # Decode token
        token_status, token_contents = decode_token(jwt_token)

        # Check if token is valid
        if not token_status == TokenState.VALID:
            # If the token is not valid, return the error message with code 401
            return make_response(token_contents, 401)

        # Token is valid

        # Execute function as normal
        """
        This needs to be a flask Response, use `make_response` for this
        """
        func_response: Response = func(*args, **kwargs)

        try:
            # Renew token
            # TODO: Properly renew the token
            token, expire = encode_token(token_contents)
            # func_response.set_cookie('jwt', token, expires=expire, httponly=True, samesite="Strict")
            # func_response.set_cookie("jwt", token, expires=expire, samesite="None", secure=True, httponly=False) # TODO: Production
            func_response.set_cookie("jwt", token, expires=expire, samesite="Lax", secure=False, httponly=False)
        except AttributeError:
            raise AttributeError(
                "Wrapped function should return a Response, but got {} instead", type(func_response))

        return func_response

    return check_auth

class AuthCheck(Resource):
    def route():
        return "/check_auth"

    # @auth_valid
    def post(self) -> Response:
        # Check if cookie present
        if 'jwt' not in request.cookies:
            response = make_response("Could not find jwt authentication", 401)
            return response

        # Cookie is present
        jwt_token = request.cookies['jwt']

        # Decode token
        token_status, token_contents = decode_token(jwt_token)

        print(token_status, token_contents, flush=True)

        # Check if token is valid
        if not token_status == TokenState.VALID:
            # If the token is not valid, return the error message with code 401
            return make_response(token_contents, 401)

        token, expire = encode_token(token_contents["user_id"])

        return make_response("Auth valid", 200)