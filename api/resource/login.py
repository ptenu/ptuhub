from datetime import datetime, timedelta

import api.middleware.authentication as auth
import falcon
import jwt
from cryptography.hazmat.primitives import serialization
from falcon import HTTP_201, HTTP_204
from falcon.errors import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPUnauthorized
from model.Contact import Contact
from passlib.hash import argon2
from services.auth import PRIV_KEY, PUB_KEY, User, token_refresh
from settings import config


class PasswordResource:
    def change_password(self, contact: Contact, new_password: str):
        """
        Change a contact password
        """
        contact.password_hash = argon2.hash(new_password)
        self.session.commit()

    def on_put_self(self, req, resp):
        """
        Change your own password
        """

        if req.context.user is None:
            raise HTTPUnauthorized

        try:
            new_password = req.media.password
        except KeyError:
            raise HTTPBadRequest(description="You must provide a new password.")

        self.change_password(req.context.user, new_password)

        resp.status = HTTP_204

    @falcon.before(auth.EnforceRoles, ["global.admin"])
    def on_put_contact(self, req, resp, contact_id):
        """
        Change a specified contact's password
        """

        contact = self.session.query(Contact).get(contact_id)
        if contact is None:
            raise HTTPNotFound

        try:
            new_password = req.media["password"]
        except KeyError:
            raise HTTPBadRequest(description="You must provide a new password.")

        self.change_password(contact, new_password)

        resp.status = HTTP_204


class TokenResource:
    def on_get_pk(self, req, resp):
        key = PUB_KEY.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        resp.data = key
        resp.content_type = falcon.MEDIA_TEXT
