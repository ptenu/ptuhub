from email.policy import default
import secrets
from datetime import datetime, timedelta

from blake3 import blake3
from settings import config
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import *
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func, text

from model import Model

SK = config.get("default", "secret")


class Session(Model):
    """
    A session exists for all visitors
    """

    __tablename__ = "csrf_sessions"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))

    user_agent_hash = Column(VARCHAR(64), nullable=False)
    remote_addr = Column(INET, nullable=False)
    source = Column(VARCHAR(1024), nullable=False)
    created = Column(TIMESTAMP, default=func.now())
    last_used = Column(TIMESTAMP, default=func.now(), server_onupdate="now()")
    trusted = Column(BOOLEAN, default=False, nullable=False)
    contact_id = Column(
        INTEGER, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True
    )
    user = relationship("Contact", backref="sessions")

    def entrust(self, contact=None):
        self.trusted = True

        if contact is not None:
            self.user = contact

    def detrust(self):
        self.trusted = False

    def set_user_agent(self, ua: str) -> str:
        h = blake3(bytes(ua, "utf-8"), key=bytes(SK, "utf-8"))
        self.user_agent_hash = h.hexdigest()
        return self.user_agent_hash


class Request(Model):
    """
    A single request
    """

    __tablename__ = "requests"

    id = Column(INTEGER, primary_key=True)

    started = Column(TIMESTAMP, default=func.now())
    finished = Column(TIMESTAMP, default=None, nullable=True)
    duration = Column(FLOAT(8, True, 6), nullable=True)
    session_id = Column(
        UUID, ForeignKey("csrf_sessions.id", ondelete="CASCADE"), nullable=True
    )
    host = Column(VARCHAR(256))
    path = Column(VARCHAR(1024))
    method = Column(VARCHAR(6), nullable=False)
    trusted = Column(BOOLEAN, default=False, nullable=False)
    response_code = Column(INTEGER, nullable=True)
    contact_id = Column(
        INTEGER, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True
    )
    return_hash = Column(VARCHAR(64))

    user = relationship("Contact", backref="requests")
    session = relationship(Session, backref="requests")

    def end(self, code=200):
        self.finished = datetime.now()
        self.response_code = code

        if self.finished is None or self.started is None:
            return

        delta: timedelta = self.finished - self.started
        self.duration = delta.total_seconds()

    def generate_hash(self) -> str:
        random = secrets.token_bytes(32)
        h = blake3(random, key=bytes(SK, "utf-8"))
        self.return_hash = h.hexdigest()
        return self.return_hash
