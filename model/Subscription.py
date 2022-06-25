from email.policy import default
import uuid
from datetime import date, datetime, timedelta
from enum import Enum

from dateutil.relativedelta import relativedelta
from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship
from model.Schema import Schema
from services.permissions import RoleTypes, user_has_position, user_has_role

from model import Model
from model import db


class Payment(Model):

    __tablename__ = "payments"

    class Types(Enum):
        SUBS = "membership"
        DONA = "donation"
        SALE = "purchase"
        ADHC = "ad-hoc"
        RNEW = "renewal"

    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    stripe_payment_intent_id = Column(String(52), nullable=True)
    stripe_charge_id = Column(String(52), nullable=True)
    status = Column(String(50), nullable=False, default="created")
    created_on = Column(Date)
    last_updated = Column(DateTime)
    amount = Column(Integer, nullable=False, default=100)
    type = Column(
        EnumColumn(Types, name="payment_types"), nullable=False, default=Types.SUBS
    )
    method_type = Column(String(20))
    method_last4 = Column(String(4))

    contact = relationship(
        "Contact", backref=backref("payments", order_by=created_on.desc())
    )

    def view_guard(self, user):
        if user is None:
            return False

        if user.id == self.contact_id:
            return True

        try:
            user_has_position(
                user,
                (RoleTypes.CHAIR, RoleTypes.SEC, RoleTypes.TRUST, RoleTypes.TRES),
                union=True,
            )
            return True
        except:
            try:
                user_has_position(
                    user,
                    (RoleTypes.CHAIR, RoleTypes.SEC, RoleTypes.TRES),
                    branch=self.contact.branch,
                )
                return True
            except:
                return False

    def __schema__(self):
        return Schema(
            self,
            ["id", "status", "amount", "method_type", "method_last4"],
            custom_fields={"date": self.created_on.isoformat()},
        )


class Membership(Model):

    __tablename__ = "memberships"

    class Statuses(Enum):
        PENDING = "pending"
        UNPAID = "unpaid"
        PAID = "paid"
        SUSPENDED = "suspended"
        REJECTED = "rejected"
        CANCELLED = "cancelled"

    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(
        EnumColumn(Statuses, name="membership_statuses"),
        nullable=False,
        default=Statuses.PENDING,
    )
    payment_id = Column(
        Integer, ForeignKey("payments.id", ondelete="SET NULL", onupdate="CASCADE")
    )

    contact = relationship(
        "Contact", backref=backref("memberships", order_by=period_start.desc())
    )
    payment = relationship(
        Payment, backref=backref("memberships", order_by=period_start.desc())
    )

    def __init__(self, contact, start_date: date):
        self.contact = contact
        self.period_start = start_date
        self.period_end = start_date + relativedelta(months=1)
        self.month = start_date.month
        self.year = start_date.year


class MembershipCard(Model):
    __tablename__ = "cards"

    id = Column(String(20), primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    date = Column(Date, default=datetime.today())
    status = Column(String(10), default="generated")

    contact = relationship("Contact", backref="membership_cards")

    def __init__(self, contact):
        self.contact = contact
        self.id = self.generate_card_number()

    def generate_card_number(self):
        name = self.contact.family_name[:4].upper()
        urn = self.contact.membership_number
        return f"{str(self.date.month).zfill(3)}{name}{self.date.year}{urn}0"


class Donation(Model):

    __tablename__ = "donations"

    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    amount = Column(Integer, nullable=False, default=500)
    frequency = Column(Integer, nullable=False, default=1)

    contact = relationship("Contact", backref="donations")
