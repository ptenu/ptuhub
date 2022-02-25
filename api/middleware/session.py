from datetime import datetime, timedelta

from blake3 import blake3
from falcon.errors import HTTPUnauthorized
from jwt import ExpiredSignatureError
from model import db
from model.Session import Request, Session
from settings import config

SK = config.get("default", "secret")
ENV = config.get("default", "env")

NO_VALIDATION_URLS = ("/session", "/")


class SessionManager:
    def __validate_hash(self, session_id, client_id, resp):
        cutoff = datetime.now() - timedelta(seconds=30)
        request = (
            db.query(Request)
            .filter(Request.session_id == session_id)
            .filter(Request.started > cutoff)
            .filter(Request.return_hash == client_id)
            .first()
        )

        if request is not None:
            return

        requests = (
            db.query(Request)
            .filter(Request.session_id == session_id)
            .filter(Request.return_hash != None)
            .order_by(Request.started.desc())
            .limit(3)
            .all()
        )

        valid_codes = list(map(lambda r: r.return_hash, requests))
        if client_id in valid_codes:
            return

        if ENV == "dev":
            resp.set_header("x-dev-message", "Client ID was invalid")
            return

        raise HTTPUnauthorized(title="Invalid token", description="Client Id mismatch")

    def process_request(self, req, resp):
        """
        Validate any tokens included in the request and block if
        invalid.
        If its all good, then include the session and contact in the
        request.context object.
        """

        if req.path in NO_VALIDATION_URLS:
            req.context.user = None
            return

        # Get any headers we might need
        session_id = req.get_header("X-Session-Id")
        client_hash = req.get_header("X-Client-Id")
        verification_code = req.get_header("X-Verification-Code")

        # Get the session
        if session_id is None:
            raise HTTPUnauthorized(
                title="Invalid token", description="Missing session ID header"
            )

        if client_hash is None:
            raise HTTPUnauthorized(
                title="Invalid token", description="Missing client ID header"
            )

        try:
            session = db.query(Session).get(session_id)
            assert session is not None
        except:
            raise HTTPUnauthorized(
                title="Invalid token", description="Invalid session ID"
            )

        try:

            h = blake3(bytes(req.user_agent, "utf-8"), key=bytes(SK, "utf-8"))
            assert session.remote_addr == req.remote_addr
            assert session.source == req.host
            assert session.user_agent_hash == h.hexdigest()

        except AssertionError:
            raise HTTPUnauthorized(
                title="Invalid token", description="Session mismatch"
            )

        request = Request()
        request.session = session
        request.started = datetime.now()
        request.host = req.host
        request.path = req.path
        request.method = req.method
        request.trusted = session.trusted
        db.add(request)

        req.context.session = session
        req.context.request = request
        session.last_used = datetime.now()

        req.context.user = session.user
        request.user = session.user

        self.__validate_hash(session_id, client_hash, resp)

        db.commit()

    def process_response(self, req, resp, resource, req_succeeded):
        """
        Update the information on the request
        """

        if req.method == "OPTIONS":
            return

        if not hasattr(req.context, "request"):
            return

        request: Request = req.context.request

        code = resp.status[:3]

        request.end(int(code))
        db.commit()

        if resp.status == "401 Unauthorized":
            return

        client_hash = request.generate_hash()
        resp.set_header("X-Client-Id", client_hash)
        resp.set_header("Access-Control-Expose-Headers", "X-Client-Id, X-Dev-Message")
        db.commit()
