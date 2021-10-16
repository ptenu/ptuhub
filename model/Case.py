from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Enum as EnumColumn
from enum import Enum

from model import Model


class Case(Model):

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    ref = Column(String(10), unique=True, nullable=False)
    priority = Column(Integer, nullable=False, default=5)

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())
    _created_by = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    created_by = relationship(
        "Contact", backref="cases_created", foreign_keys=[_created_by]
    )

    @property
    def status(self):
        try:
            return self.status_history[0].name
        except:
            return None


class CaseContacts(Model):
    __tablename__ = "case_contacts"

    case_id = Column(
        Integer, ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    full_name = Column(String(255), nullable=False)
    relation = Column(String(25), nullable=False)

    contact = relationship("Contact", backref="related_cases")
    case = relationship("Case", backref="contacts")

    def __init__(self, contact, relation: str, case=None):
        self.contact = contact.id
        self.full_name = contact.give_name + " " + contact.family_name
        self.relation = relation

        if case is not None:
            self.case_id = case.id


class CaseStatus(Model):

    __tablename__ = "case_status"

    class Statuses(Enum):
        ACTIVE = "active"
        WAITING = "waiting for member"
        REQUIRES_ACTION = "waiting for response"
        ON_HOLD = "on hold"
        RESOLVED = "resolved"
        NO_ACTION = "no further action"
        CLOSED = "closed"
        ARCHIVED = "archived"

    id = Column(Integer, primary_key=True)
    case_id = Column(
        Integer,
        ForeignKey("cases.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(EnumColumn(Statuses, name="case_status_names"), nullable=False)
    _created_on = Column(DateTime, default=datetime.now(), nullable=False)

    case = relationship(
        Case, backref=backref("status_history", order_by=_created_on.desc())
    )


class CaseText(Model):

    __tablename__ = "case_text"

    class Types(Enum):
        COMMENT = "comment"
        DESCRIPTION = "description"
        DETAIL = "detail"
        INCIDENT = "incident"
        STATEMENT = "statement"
        UPDATE = "update"

    id = Column(Integer, primary_key=True)
    case_id = Column(
        Integer,
        ForeignKey("cases.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    started = Column(DateTime)
    finished = Column(DateTime)
    location = Column(String(255))
    statement_by = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    _created_on = Column(DateTime, default=datetime.now(), nullable=False)
    _created_by = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    statement_by = relationship(
        "Contact", backref="statements", foreign_keys=[statement_by]
    )
    created_by = relationship(
        "Contact", backref="case_text_added", foreign_keys=[_created_by]
    )
    case = relationship(Case, backref=backref("texts", order_by=_created_on.desc()))