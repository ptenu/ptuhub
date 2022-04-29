from falcon import HTTP_201, HTTP_204
from falcon.errors import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPUnauthorized
from model.Contact import Contact
from passlib.hash import argon2
from password_strength import PasswordPolicy
from services.permissions import InvalidPermissionError, user_has_role
from settings import config


class PasswordResource:
    def change_password(self, contact: Contact, new_password: str):
        """
        Change a contact password
        """
        policy = PasswordPolicy.from_names(
            length=8, uppercase=1, numbers=2, special=1, strength=0.33
        )

        password_test = policy.test(new_password)
        if len(password_test) > 0:
            raise HTTPBadRequest(description="Please chose a stronger password")

        contact.password_hash = argon2.hash(new_password)
        self.session.commit()

    def on_put_self(self, req, resp):
        """
        Change your own password
        """

        if req.context.user is None:
            raise HTTPUnauthorized

        try:
            body = req.get_media()
            new_password = body["password"]
        except KeyError:
            raise HTTPBadRequest(description="You must provide a new password.")

        self.change_password(req.context.user, new_password)

        resp.status = HTTP_204
        resp.context.clear_sessions = True

    def on_put_contact(self, req, resp, contact_id):
        """
        Change a specified contact's password
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        contact = self.session.query(Contact).get(contact_id)
        if contact is None:
            raise HTTPNotFound

        try:
            body = req.get_media()
            new_password = body["password"]
        except KeyError:
            raise HTTPBadRequest(description="You must provide a new password.")

        self.change_password(contact, new_password)

        resp.status = HTTP_204
