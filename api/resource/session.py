import falcon
from falcon import HTTP_201, HTTP_204
from falcon.errors import (
    HTTPBadRequest,
    HTTPNotFound,
    HTTPNotImplemented,
)
from model.Contact import Contact
from model.Session import Session, Request
from passlib.hash import argon2
from settings import config
from blake3 import blake3
from datetime import datetime

SK = config.get("default", "secret")


class SessionResource:
    def _get_user_last_session(self, req, contact: Contact):
        h = blake3(bytes(req.user_agent, "utf-8"), key=bytes(SK, "utf-8"))
        remote_address = req.access_route[-1]
        session = (
            self.session.query(Session)
            .filter(Session.contact_id == contact.id)
            .filter(Session.user_agent_hash == h.hexdigest())
            .filter(Session.source == req.host)
            .filter(Session.remote_addr == remote_address)
            .order_by(Session.last_used.desc())
            .first()
        )

        return session

    def on_post(self, req, resp):
        """
        Create a session from login details or a refresh token
        """

        tokens = {}

        body = req.get_media()
        session = Session()
        session.remote_addr = req.access_route[-1]
        session.source = req.host
        session.set_user_agent(req.user_agent)

        if "endpoint" in body:
            raise HTTPNotImplemented

        if "username" in body and "password" in body:
            contact: Contact = (
                self.session.query(Contact)
                .filter(Contact.prefered_email == str(body["username"]).upper())
                .first()
            )

            if contact is None:
                raise HTTPNotFound(
                    description="The username or password you provided was incorrect."
                )

            if contact.password_hash is None or contact.account_blocked:
                raise HTTPBadRequest(
                    description="You are not currently able to log in using this account. Please speak to an administrator."
                )

            result = argon2.verify(body["password"], contact.password_hash)
            if result == False:
                raise HTTPNotFound(
                    description="The username or password you provided was incorrect."
                )

            last_session = self._get_user_last_session(req, contact)
            if last_session is not None:
                session = last_session

            session.user = contact
            session.entrust()

        if session.id is None:
            self.session.add(session)

        session.last_used = datetime.now()

        request = Request()
        request.session = session
        request.host = req.host
        request.path = req.path
        request.method = req.method
        request.trusted = session.trusted
        self.session.add(request)

        req.context.request = request

        if session.user is not None:
            request.user = session.user

        self.session.commit()
        resp.media = {"session_id": session.id}
        resp.set_cookie("SESSION_ID", session.id)
