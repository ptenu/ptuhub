from datetime import datetime
from enum import Enum, auto

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from model import Model, db
from model.Contact import Contact
from model.Organisation import Branch, Committee
from services.permissions import RoleTypes, e2b, trusted_user, user_has_position


class EmailMessage(Model):

    __tablename__ = "emails"

    class Statuses(Enum):
        DRAFT = auto()
        SCHEDULED = auto()
        SENT = auto()
        ARCHIVED = auto()
        RENDERING = auto()
        SENDING = auto()

    class Priorities(Enum):
        TRANSACTIONAL = 0
        CONSTITUTIONAL = 10
        MEMBERSHIP = 20
        MARKETING = 100
        REPORT = 50

    id = Column(Integer, primary_key=True)
    subject = Column(String(1024), nullable=False)
    message = Column(Text)
    template = Column(String(1024), nullable=False, default="basic")
    send_after = Column(DateTime, default=None, nullable=True)
    _status = Column(EnumColumn(Statuses, name="email_status"), default=Statuses.DRAFT)
    priority = Column(
        EnumColumn(Priorities), nullable=False, default=Priorities.MARKETING
    )

    # Meta
    _created_on = Column(DateTime, default="NOW()")
    _updated_on = Column(DateTime, onupdate="NOW()")
    _created_by = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    created_by = relationship(
        "Contact", backref="sent_emails", foreign_keys=[_created_by]
    )

    def view_guard(self, user):
        if not e2b(trusted_user(user)):
            return False

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value


class EmailRecipient(Model):

    __tablename__ = "email_recipients"

    class Types(Enum):
        CONTACT = auto()
        BRANCH = auto()
        COMMITTEE = auto()
        SECTION = auto()

    message_id = Column(
        Integer, ForeignKey("emails.id", ondelete="CASCADE"), primary_key=True
    )
    type = Column(EnumColumn(Types), primary_key=True)
    recipient_id = Column(Integer, primary_key=True)

    email = relationship(EmailMessage, backref="recipients")

    @property
    def name(self):
        """
        Get the name of the recipient.
        """

        if self.type is self.Types.CONTACT:
            contact: Contact = db.get(Contact, self.recipient_id)
            return contact.name

        if self.type is self.Types.BRANCH:
            branch: Branch = db.get(Branch, self.recipient_id)
            return branch.formal_name

        if self.type is self.Types.COMMITTEE:
            committee: Committee = db.get(Committee, self.recipient_id)
            return committee.name


class EmailDelivery(Model):

    __tablename__ = "email_deliveries"

    class Statuses(Enum):
        PENDING = auto()
        SENT = auto()
        DELIVERED = auto()
        READ = auto()

    message_id = Column(
        Integer, ForeignKey("emails.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL"),
        primary_key=True,
    )
    status = Column(
        EnumColumn(Statuses, name="delivery_statuses"),
        nullable=False,
        default=Statuses.PENDING,
    )

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())

    email = relationship(EmailMessage, backref="deliveries")
    contact = relationship("Contact", backref="emails_recieved")

    def __init__(self, email_id, contact_id):
        self.contact_id = contact_id
        self.message_id = email_id
