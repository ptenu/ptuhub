import os
import uuid
from datetime import datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from falcon.errors import HTTPForbidden, HTTPUnauthorized
from model import db
from model.Contact import Contact
from settings import config


def generate_key_pair():
    PUBLIC_EXPONENT = 65537
    KEY_SIZE = 2048

    private_key = rsa.generate_private_key(PUBLIC_EXPONENT, KEY_SIZE)
    public_key = private_key.public_key()

    key_path = os.path.join(os.getcwd(), "keys")
    now = int(datetime.now().timestamp())
    pub_name = f"{str(now)}-pub.pem"
    priv_name = f"{str(now)}-priv.pem"
    if not os.path.isdir(key_path):
        os.mkdir(key_path)

    with open(os.path.join(key_path, priv_name), "wb") as f:
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(
                bytes(config["default"].get("secret", "--secret--"), "utf-8")
            ),
        )

        f.write(priv_pem)

    with open(os.path.join(key_path, pub_name), "wb") as f:
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        f.write(pub_pem)

    return private_key, public_key


def get_current_keys():
    key_path = os.path.join(os.getcwd(), "keys")
    if not os.path.isdir(key_path):
        return generate_key_pair()

    files = []
    for (_, _, filenames) in os.walk(key_path):
        files.extend(filenames)
        break

    if len(files) < 1:
        return generate_key_pair()

    files.sort(reverse=True)

    pub_file = None
    priv_file = None

    for f in files:
        if str(f).endswith("priv.pem") and priv_file is None:
            priv_file = f

        elif str(f).endswith("pub.pem") and pub_file is None:
            pub_file = f

        if priv_file is not None and pub_file is not None:
            break

    with open(os.path.join(key_path, priv_file), "rb") as f:
        priv_key = serialization.load_pem_private_key(
            f.read(),
            password=bytes(
                bytes(config["default"].get("secret", "--secret--"), "utf-8")
            ),
        )

    with open(os.path.join(key_path, pub_file), "rb") as f:
        pub_key = serialization.load_pem_public_key(f.read())

    return priv_key, pub_key


PRIV_KEY, PUB_KEY = get_current_keys()


class User:
    """
    A user class to be instantiated for each request.
    This is not persisted to the database.
    """

    authenticated: bool = False
    anonymous: bool = True
    contact: Contact = None
    roles = []

    def __init__(self, contact: Contact = None):
        self.valid_for = timedelta(minutes=10)
        self.roles = []

        if contact is not None:
            self.contact = contact
            self.anonymous = False
            self.authenticated = True

            for r in contact.roles:
                self.roles.append(r.name)

    def get_claims(self):
        exp = datetime.now() + self.valid_for
        claims = {
            "sub": self.contact.id,
            "iss": "ptu-hub-api",
            "type": "auth",
            "email": self.contact.prefered_email,
            "name": self.contact.name,
            "iat": datetime.now().timestamp(),
            "nbf": (datetime.now() - timedelta(seconds=10)).timestamp(),
            "exp": exp.timestamp(),
            "anon": True,
            "roles": self.roles,
        }

        if self.contact is not None:
            claims["email"] = self.contact.prefered_email
            claims["anon"] = False

        return claims

    def get_auth_token(self):
        return jwt.encode(
            self.get_claims(),
            PRIV_KEY,
            algorithm="RS256",
        )

    def get_refresh_token(self):
        return jwt.encode(
            {
                "sub": self.contact.id,
                "type": "refresh",
                "iss": "ptu-hub-api",
                "iat": datetime.now().timestamp(),
                "nbf": (datetime.now() - timedelta(seconds=10)).timestamp(),
                "exp": (datetime.now() + timedelta(days=7)).timestamp(),
            },
            PRIV_KEY,
            algorithm="RS256",
        )


def get_contact_from_token(token: str):
    if token.startswith("Bearer"):
        token = token[7:]
    claims = jwt.decode(token, PUB_KEY, algorithms=["RS256"])

    if claims["iss"] != "ptu-hub-api":
        raise HTTPUnauthorized(
            title="Invalid token", description="Invalid authentication token"
        )

    try:
        if claims["anon"] == True:
            return None
    except KeyError:
        pass

    return db.query(Contact).get(claims["sub"])


def token_refresh(token: str):
    """
    Takes a refresh token and returns a new authentication token for that user.
    """

    if token.startswith("Bearer"):
        token = token[7:]

    claims = jwt.decode(token, PUB_KEY, algorithms=["RS256"])

    if claims["iss"] != "ptu-hub-api":
        raise HTTPUnauthorized(
            title="Invalid token", description="Invalid refresh token"
        )

    if claims["type"] != "refresh":
        raise HTTPUnauthorized(
            title="Invalid token", description="Invalid refresh token"
        )

    person = db.query(Contact).get(claims["sub"])
    if person is None:
        raise HTTPUnauthorized(
            title="Invalid token", description="Invalid refresh token"
        )
    user = User(person)

    return user.get_auth_token()
