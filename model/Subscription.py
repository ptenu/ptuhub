from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from enum import Enum

from sqlalchemy import Boolean, Column, Date, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, Text, BigInteger
from sqlalchemy.orm import relationship, backref

from model import Model, Session as db


class Subscription(Model):

    __tablename__ = "subscriptions"

    class Statuses(Enum):
        PENDING = "pending"
        ACTIVE = "active"
        NEW = "new"
        CANCELLED = "cancelled"
        REJECTED = "rejected"
        PAYMENT_FAILED = "failed payment"
        LAPSED = "lapsed"
        ARREARS = "in arrears"
        SUSPENDED = "suspended"
        INCOMPLETE = "incomplete"

    class Types(Enum):
        STANDARD = "standard"
        ASSOCIATE = "supporter"
        AFFILIATE = "affiliated organisation"

    id = Column(String(255), primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    start_date = Column(Date, nullable=False, default=date.today())
    renewal_date = Column(
        Date, nullable=False, default=date.today() + timedelta(days=30)
    )
    stripe_price_id = Column(String(255), nullable=True)
    stripe_coupon_id = Column(String(255), nullable=True)
    base_rate = Column(Integer, nullable=False, default=0)
    discount = Column(Integer, default=0, nullable=False)
    type = Column(
        EnumColumn(Types, name="subs_types"), nullable=False, default=Types.STANDARD
    )
    status = Column(
        EnumColumn(Statuses, name="subs_statuses"),
        nullable=False,
        default=Statuses.PENDING,
    )

    contact = relationship(
        "Contact", backref=backref("subscriptions", order_by=start_date.desc())
    )

    def __init__(self, contact):
        self.contact = contact
        self.start_date = date.today()
        self.renewal_date = date.today() + relativedelta(months=1)


class Activity(Model):
    __tablename__ = "activity"

    class Codes(Enum):
        JOINED = "join"
        PAYMENT = "payment"
        FAILED_PAYMENT = "failed payment"
        AD_HOC_PAYMENT = "ad hoc payment"
        CANCELLED = "cancelation"
        ISSUED_CARD = "card issue"
        RENEWED = "renewal"
        SUSPENDED = "suspension"
        REJECTED = "rejection"

    SET_TO = {
        Codes.JOINED: Subscription.Statuses.PENDING,
        Codes.PAYMENT: Subscription.Statuses.ACTIVE,
        Codes.FAILED_PAYMENT: Subscription.Statuses.PAYMENT_FAILED,
        Codes.CANCELLED: Subscription.Statuses.CANCELLED,
        Codes.RENEWED: Subscription.Statuses.ACTIVE,
        Codes.SUSPENDED: Subscription.Statuses.SUSPENDED,
        Codes.REJECTED: Subscription.Statuses.REJECTED,
    }

    id = Column(Integer, primary_key=True)
    stripe_object_id = Column(String(255), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.now())
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    type = Column(EnumColumn(Codes, name="activity_codes"))
    subscription_id = Column(
        String(255),
        ForeignKey("subscriptions.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    value = Column(Integer, nullable=True, default=None)
    summary = Column(String, nullable=True)
    meta = Column(Text, nullable=True)

    contact = relationship("Contact", backref="activity")
    subscription = relationship(Subscription, backref="activity")

    def __init__(self, contact, code, subscription=None):
        self.contact = contact
        self.type = code

        if subscription is not None:
            self.subscription = subscription

            if hasattr(self.SET_TO, code):
                self.subscription.status = self.SET_TO[code]

            if self.subscription.start_date < datetime.now() - timedelta(weeks=4):
                return

            if code is self.Codes.PAYMENT:
                last_payment = (
                    db.query(Activity)
                    .filter(Activity.contact_id == self.contact_id)
                    .filter(Activity.subscription_id == self.subscription_id)
                    .filter(Activity.type == self.Codes.PAYMENT)
                    .order_by(Activity.timestamp.desc())
                    .first()
                )

                if last_payment is None:
                    self.subscription.status = Subscription.Statuses.NEW

            if code is self.Codes.FAILED_PAYMENT:
                last_payment = (
                    db.query(Activity)
                    .filter(Activity.contact_id == self.contact_id)
                    .filter(Activity.subscription_id == self.subscription_id)
                    .filter(Activity.type == self.Codes.PAYMENT)
                    .order_by(Activity.timestamp.desc())
                    .first()
                )

                if last_payment is None:
                    self.subscription.status = Subscription.Statuses.INCOMPLETE

                if last_payment.timestamp < datetime.now() - timedelta(weeks=6):
                    self.subscription.status = Subscription.Statuses.ARREARS


class MembershipCard(Model):
    __tablename__ = "cards"

    id = Column(String(20), primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    date = Column(Date, default=datetime.today())
    barcode_img_id = Column(String(10), ForeignKey("files.id"))

    contact = relationship("Contact", back_populates="membership_cards")

    def __init__(self, contact):
        self.contact = contact
        self.id = self.generate_card_number()

    def generate_card_number(self):
        name = self.contact.family_name[:4].upper()
        urn = self.contact.membership_number
        return f"{str(self.date.month).zfill(3)}{name}{self.date.year}{urn}0"
