from datetime import datetime, timedelta

from blake3 import blake3
from falcon.errors import HTTPUnauthorized
from services.cognito import validate_token
from settings import config

SK = config.get("default", "secret")
ENV = config.get("default", "env")
BEARER = "Bearer "


class SessionManager:
    def process_request(self, req, resp):
        """
        Validate any tokens included in the request and block if
        invalid.
        """

        if req.method == "OPTIONS":
            return

        # Get any headers we might need
        access_token: str = req.auth

        try:
            access_token = access_token.split(" ")[-1]
            contact = validate_token(access_token)
        except Exception as e:
            print(str(e))
            raise HTTPUnauthorized

        req.context.user = contact

    def process_response(self, req, resp, resource, req_succeeded):
        """
        Update the information on the request
        """

        if "Access-Control-Allow-Origin" not in resp.headers:
            source = req.host
            if req.get_header("Origin") is not None:
                source = req.get_header("Origin")

            resp.append_header("Access-Control-Allow-Origin", source)
            resp.append_header("Access-Control-Allow-Credentials", "true")
            resp.append_header(
                "Access-Control-Allow-Methods", "GET,PUT,PATCH,POST,DELETE,OPTIONS"
            )
            resp.append_header(
                "Access-Control-Allow-Headers", "content-type, x-client-id"
            )
            resp.append_header("Vary", "Origin")

        if req.method == "OPTIONS":
            return
