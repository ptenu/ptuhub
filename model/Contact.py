from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Boolean, Column, Date, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, Text, BigInteger
from sqlalchemy.orm import relationship

from model import Model


class Contact(Model):

    __tablename__ = "contacts"

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())

    # Main Fields
    id = Column(Integer, primary_key=True, index=True)
    given_name = Column(String(255))
    family_name = Column(String(255))
    other_names = Column(String(255))
    first_language = Column(String(20))
    pronouns = Column(String(10))
    date_of_birth = Column(Date)
    avatar_id = Column(String(10))

    # Membership
    membership_number = Column(String(15))
    joined_on = Column(Date)
    membership_type = Column(String(1))
    stripe_customer_id = Column(String(52))
    postcode = Column(String(8), nullable=True)

    # Contact
    prefered_email = Column(String(1024), ForeignKey("contact_emails.address"))
    prefered_phone = Column(String(15), ForeignKey("contact_numbers.number"))

    # Account
    password_hash = Column(String(255), nullable=True)
    account_blocked = Column(Boolean, nullable=False, default=False)

    email = relationship(
        "EmailAddress", backref="main_for", foreign_keys=[prefered_email]
    )
    telephone = relationship(
        "TelephoneNumber", backref="main_for", foreign_keys=[prefered_phone]
    )


class EmailAddress(Model):

    __tablename__ = "contact_emails"

    # Main
    address = Column(String(1024), primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    verified = Column(Boolean, default=False, nullable=False)
    blocked = Column(Boolean, nullable=False, default=False)

    # Relationships
    contact = relationship(
        Contact, backref="email_addresses", foreign_keys=[contact_id]
    )

    def __init__(self, contact, address):
        self.contact = contact
        self.address = address.upper()

    def __str__(self):
        return self.address.upper()

    @property
    def is_internal(self):
        domain = str(self.address).split("@")[1]
        return domain == "peterboroughtenants.org"

    @property
    def formated_address(self):
        name = (
            str(self.contact.family_name).upper()
            + ", "
            + str(self.contact.given_name).capitalize()
        )


class TelephoneNumber(Model):

    __tablename__ = "contact_numbers"

    # Main
    number = Column(String(15), primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    verified = Column(Boolean, default=False, nullable=False)
    blocked = Column(Boolean, nullable=False, default=False)

    # Relationships
    contact = relationship(Contact, backref="phone_numbers", foreign_keys=[contact_id])


class ContactAddress(Model):

    __tablename__ = "contact_addresses"

    class Tenure(Enum):
        RENT_SOCIAL = "private rented"
        RENT_PRIVATE = "social housing"
        LODGER = "living with landlord"
        LICENSEE = "licensee"
        OCCUPIER = "non-legal occupier"
        OWNER_OCCUPIER = "owner occupier"
        LANDLORD = "landlord"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    uprn = Column(
        BigInteger,
        ForeignKey("addresses.uprn", onupdate="CASCADE", ondelete="SET NULL"),
    )
    custom_address = Column(Text)
    mail_to = Column(Boolean, nullable=False, default=True)
    tenure = Column(EnumColumn(Tenure))
    active = Column(Boolean, nullable=False, default=True)

    # Table relation
    # Relationships
    contact = relationship(Contact, backref="addresses")


class Consent(Model):

    __tablename__ = "consents"

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())

    # Main
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    consent_id = Column(Integer, primary_key=True, autoincrement=True)
    group = Column(String(25), nullable=False)
    code = Column(String(25), nullable=False)
    source = Column(String(25))
    expires = Column(Date)
    wording = Column(Text)

    # Relationships
    contact = relationship(Contact, backref="consents")


class Note(Model):

    __tablename__ = "contact_notes"

    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    content = Column(Text)

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())
    _created_by = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    # Relationships
    contact = relationship(Contact, backref="notes", foreign_keys=[contact_id])
    contact = relationship(Contact, backref="notes_created", foreign_keys=[_created_by])


class VerifyToken(Model):

    __tablename__ = "verify_contact_tokens"

    class Types(Enum):
        EMAIL = "email"
        PHONE = "phone"

    type = Column(EnumColumn(Types), primary_key=True)
    id = Column(String(1024), primary_key=True)
    hash = Column(String(256), unique=True, nullable=False)
    expires = Column(
        DateTime,
        default=datetime.now() + timedelta(minutes=15),
        onupdate=datetime.now() + timedelta(minutes=15),
    )


class Role(Model):

    __tablename__ = "auth_roles"

    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    name = Column(String(20), primary_key=True)

    contact = relationship(Contact, backref="roles")
