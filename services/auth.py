import uuid, json, jwt
from settings import config
from model.Contact import Contact
from datetime import timedelta, datetime
from model import Session as db


class User:
    """
    A user class to be instantiated for each request.
    This is not persisted to the database.
    """

    id: str = ""
    authenticated: bool = False
    anonymous: bool = True
    contact: Contact = None

    def __init__(self, id: str = None, contact: Contact = None):
        self.valid_for = timedelta(minutes=15)

        if contact is not None:
            self.contact = contact
            self.anonymous = False
            self.authenticated = True

        if id is not None:
            self.id = id

        else:
            self.id = uuid.uuid4()

    def get_claims(self):
        claims = {
            "sub": self.id,
            "iss": "ptu-hub-api",
            "iat": datetime.now(),
            "nbf": datetime.now(),
            "exp": datetime.now() + self.valid_for,
            "anon": True,
        }

        if self.contact is not None:
            claims.email = self.contact.prefered_email
            claims.anon = False

        return claims

    def get_auth_token(self):
        return jwt.encode(
            self.get_claims(),
            config["default"].get("secret", "--a-key--"),
            algorithm="HS256",
        )


def get_contact_from_token(token):
    claims = jwt.decode(
        token, config["default"].get("secret", "--a-key--"), algorithms=["HS256"]
    )

    if claims.anon == True:
        return None

    return db.query(Contact).get(Contact.id == claims.sub)
