import jwt
from falcon import HTTP_201, HTTP_204
from falcon.errors import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPUnauthorized
from model.Contact import Contact
from passlib.hash import argon2
from services.auth import User
from settings import config
from datetime import datetime, timedelta


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

    def on_put_contact(self, req, resp, contact_id):
        """
        Change a specified contact's password
        """

        # TODO: Add permissions

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
    def on_get_token(self, req, resp):
        pass

    def on_post_token(self, req, resp):
        """
        Confirm a user's credentials and return an auth token
        """

        if req.context.user is not None:
            raise HTTPForbidden(description="You are already logged in.")

        body = req.media

        if "username" not in body or "password" not in body:
            raise HTTPBadRequest(description="You must provide a username and password")

        contact = (
            self.session.query(Contact)
            .filter(Contact.prefered_email == str(body["username"]).upper())
            .first()
        )

        if contact is None or contact.password_hash is None:
            raise HTTPNotFound

        result = argon2.verify(body["password"], contact.password_hash)

        if result == False:
            raise HTTPUnauthorized(
                description="The username or password you provided was incorrect."
            )

        rt = jwt.encode(
            {
                "sub": contact.id,
                "type": "refresh",
                "iss": "ptu-hub-api",
                "iat": datetime.now(),
                "nbf": datetime.now(),
                "exp": datetime.now() + timedelta(days=7),
            },
            config["default"].get("secret", "--a-key--"),
            algorithm="HS256",
        )

        user = User(contact.id, contact)
        resp.media = {
            "auth_token": user.get_auth_token(),
            "refresh_token": rt,
        }
