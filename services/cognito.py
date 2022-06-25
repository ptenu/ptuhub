import os
from base64 import b64decode

import boto3
import jwt
from jwt import PyJWKClient
import settings
from falcon import HTTPForbidden
from model import db
from model.Contact import Contact, EmailAddress, UserIdentity

REGION = settings.config["cognito"].get("region")
USER_POOL_ID = settings.config["cognito"].get("user_pool_id")
CERT_URL = (
    f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
)
ISS_CLAIM = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"

cognito = boto3.client(
    "cognito-idp",
    aws_access_key_id=settings.config["aws"].get("access_key"),
    aws_secret_access_key=settings.config["aws"].get("secret"),
    region_name=REGION,
)


def validate_token(jwt_string: str) -> Contact:
    """
    Takes an authentication token, validates it, and returns the relevant contact
    """

    key_client = PyJWKClient(CERT_URL, cache_keys=True)
    public_key = key_client.get_signing_key_from_jwt(jwt_string)

    token = jwt.decode(
        jwt_string, public_key.key, algorithms=["RS256"], issuer=ISS_CLAIM
    )
    if token["token_use"] != "access":
        raise HTTPForbidden(description="Invalid authentication token")

    identity: UserIdentity = db.get(UserIdentity, token["sub"])
    if identity is not None:
        return identity.contact

    identity = UserIdentity()
    identity.id = token["sub"]
    contact = get_contact(token["username"])
    identity.contact = contact
    db.add(identity)
    db.commit()

    return identity.contact


def get_contact(username: str) -> Contact:
    """
    Use the AWS Cognito API to get the details of an authenticated user if they are not
    already in the system.
    """

    try:
        user = cognito.admin_get_user(UserPoolId=USER_POOL_ID, Username=username)
    except:
        raise HTTPForbidden(description="Unknown user")

    attributes = user["UserAttributes"]
    email_addr = None
    for attr in attributes:
        if attr["Name"] == "email":
            email_addr = attr["Value"]
            break

    contact = None
    email = db.get(EmailAddress, email_addr.upper())
    if email is not None:
        contact = email.contact

    if contact is None:
        contact = Contact()
        for attr in attributes:
            if attr["Name"] == "given_name":
                contact.given_name = attr["Value"]
            if attr["Name"] == "family_name":
                contact.family_name = attr["Value"]

        db.add(contact)

        email = EmailAddress(contact, email_addr)
        db.add(email)

        identity = UserIdentity()
        identity.contact = contact
        identity.id = user["Username"]
        db.add(identity)

        db.commit()

    return contact
