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

    id = Column(Integer, primary_key=True)
    subject = Column(String(1024), nullable=False)
    text = Column(Text)
    html = Column(Text)
    send_after = Column(DateTime, default=None, nullable=True)
    status = Column(EnumColumn(Statuses), default=Statuses.DRAFT)
    type = Column(String(15), nullable=False, default="transactional")

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
        if e2b(trusted_user(user)) == False:
            return False


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

    message_id = Column(
        Integer, ForeignKey("emails.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL"),
        primary_key=True,
    )
    status = Column(String(20), nullable=False, default="pending")

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())

    email = relationship(EmailMessage, backref="deliveries")
    contact = relationship("Contact", backref="emails_recieved")
