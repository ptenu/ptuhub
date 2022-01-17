import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Integer, String, Text
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
    avatar_id = Column(String(10), ForeignKey("files.id"))

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
    avatar = relationship("File", backref="avatar_user", foreign_keys=[avatar_id])

    @property
    def name(self):
        return self.given_name.capitalize() + " " + self.family_name.capitalize()

    @property
    def legal_name(self):
        name = self.family_name.upper() + ", " + self.given_name.capitalize()
        if self.other_names is not None:
            name += " " + self.other_names.capitalize()
        return name

    @property
    def dict(self):
        status = None
        obj = {
            "id": self.id,
            "name": self.name,
            "legal_name": self.legal_name,
            "email": self.prefered_email,
            "membership_number": self.membership_number,
            "status": status,
        }
        return obj

    @property
    def dict_ext(self):
        status = None
        obj = {
            "id": self.id,
            "name": self.name,
            "legal_name": self.legal_name,
            "date_of_birth": self.date_of_birth.isoformat()
            if self.date_of_birth is not None
            else None,
            "joined_on": self.joined_on.isoformat()
            if self.joined_on is not None
            else None,
            "membership_type": self.membership_type,
            "account_blocked": self.account_blocked,
            "email": self.prefered_email,
            "telephone": self.prefered_phone,
            "membership_number": self.membership_number,
            "status": status,
            "created": self._created_on.isoformat()
            if self._created_on is not None
            else None,
            "updated": self._updated_on.isoformat()
            if self._updated_on is not None
            else None,
        }
        return obj

    @dict.setter
    def dict(self, values: Dict):
        for key, val in values.items():
            if val is None:
                continue
            if hasattr(self, key):
                try:
                    setattr(self, key, val)
                except:
                    pass


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

    contact = relationship(Contact, backref="address_relations")


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
