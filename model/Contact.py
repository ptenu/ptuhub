import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict
from model.Schema import Schema

from services.files import FileService
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.expression import func

from model import Model
from services.permissions import trusted_user, user_has_role


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
    membership_type = Column(String(1), default="S")
    stripe_customer_id = Column(String(52))

    # Contact
    prefered_email = Column(String(1024), ForeignKey("contact_emails.address"))
    prefered_phone = Column(String(15), ForeignKey("contact_numbers.number"))
    lives_at = Column(
        BigInteger,
        ForeignKey("contact_addresses.id", ondelete="SET NULL", onupdate="CASCADE"),
    )

    # Account
    password_hash = Column(String(255), nullable=True)
    account_blocked = Column(Boolean, nullable=False, default=False)

    # Branch relationship
    branch = relationship(
        "Branch",
        backref="contacts",
        primaryjoin="and_(Contact.lives_at == foreign(ContactAddress.id), Contact.membership_number != None)",
        secondary=(
            "join(ContactAddress, Address, ContactAddress.uprn == Address.uprn)"
        ),
        secondaryjoin="Address.branch_id == foreign(Branch.id)",
        uselist=False,
        viewonly=True,
    )

    @property
    def postcode(self):
        if self.address is None:
            return None

        if self.address.uprn is None:
            return None

        return self.address.address.postcode

    # Relationships
    email = relationship(
        "EmailAddress", backref="main_for", foreign_keys=[prefered_email]
    )
    telephone = relationship(
        "TelephoneNumber", backref="main_for", foreign_keys=[prefered_phone]
    )
    avatar = relationship("File", backref="avatar_user", foreign_keys=[avatar_id])

    def view_guard(self, user):
        if user is not None and user.id == self.id:
            return True

        try:
            user_has_role(user, "global.admin")
            return True
        except:
            try:
                user_has_role(user, "membership.admin")
            except:
                return False

    def __schema__(self):
        cf = {
            "addresses": self.address_list,
        }

        if self.branch is not None:
            cf["branch"] = {"id": self.branch.id, "name": self.branch.formal_name}

        return Schema(
            self,
            [
                "id",
                "name",
                "membership_number",
                "first_language",
                "pronouns",
                "notes",
                "email_addresses",
                "phone_numbers",
                "consents",
                "positions",
            ],
            custom_fields=cf,
        )

    @property
    def name(self):
        name = ""
        if self.given_name is not None:
            name += self.given_name.capitalize()

        if self.family_name is not None:
            name += f" {self.family_name.capitalize()}"

        return name

    @property
    def legal_name(self):
        name = self.family_name.upper() + ", " + self.given_name.capitalize()
        if self.other_names is not None:
            name += " " + self.other_names.capitalize()
        return name

    @property
    def address_list(self):
        addrs = []
        for a in self.addresses:
            addr = {}
            if not a.active:
                continue

            if a.custom_address is not None:
                addr["address"] = a.custom_address

            if a.uprn is not None:
                addr["uprn"] = a.uprn
                addr["address"] = a.address.single_line

            if a.tenure is not None:
                addr["tenure"] = str(a.tenure.value)
            addr["current_residence"] = self.lives_at == a.id
            addr["id"] = a.id
            addrs.append(addr)

        return addrs


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

    def view_guard(self, user):
        if user is not None and user.id == self.contact_id:
            return True

        try:
            user_has_role(user, "global.admin")
            return True
        except:
            try:
                user_has_role(user, "membership.admin")
            except:
                return False

    def __schema__(self):
        return Schema(
            self,
            ["address"],
            custom_fields={
                "verified": "Y" if self.verified else "N",
                "blocked": "Y" if self.blocked else "N",
            },
        )

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

        return f"{name} <{self.address.lower()}>"


class TelephoneNumber(Model):

    __tablename__ = "contact_numbers"

    # [0] Prefix, [1] Description, [3] Allowed, [4] SMS-able
    CODES = [
        ("01", "Standard Geographic", True, False),
        ("02", "Standard Geographic", True, False),
        ("03", "Standard Non-Geographic", True, False),
        ("04", "Reserved", False, False),
        ("05", "Freephone / VOIP", False, False),
        ("06", "Alternative PNS", False, False),
        ("070", "PNS", False, False),
        ("076", "Non-inclusive mobile", False, True),
        ("07", "Mobile", True, True),
        ("080", "Toll Free National", True, False),
        ("084", "Special Service", False, False),
        ("087", "Special Service", False, False),
    ]

    # Main
    number = Column(String(15), primary_key=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    verified = Column(Boolean, default=False, nullable=False)
    blocked = Column(Boolean, nullable=False, default=False)

    # Relationships
    contact = relationship(Contact, backref="phone_numbers", foreign_keys=[contact_id])

    def __init__(self, number: str) -> None:
        if number.startswith("+44"):
            number = f"0{number[3:]}"
        number = number.replace(" ", "")
        self.number = number

    def view_guard(self, user):
        if user is not None and user.id == self.contact_id:
            return True

        try:
            user_has_role(user, "global.admin")
            return True
        except:
            try:
                user_has_role(user, "membership.admin")
            except:
                return False

    def __schema__(self):
        return Schema(self, ["number", "description"])

    @property
    def description(self):
        for code in self.CODES:
            if self.number.startswith(code[0]):
                return code[1]


class ContactAddress(Model):

    __tablename__ = "contact_addresses"

    class Tenure(Enum):
        RENT_SOCIAL = "renting (social)"
        RENT_PRIVATE = "renting (private)"
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
        BigInteger, ForeignKey("addresses.uprn", onupdate="CASCADE", ondelete="CASCADE")
    )
    custom_address = Column(Text)
    mail_to = Column(Boolean, nullable=False, default=True)
    tenure = Column(EnumColumn(Tenure))
    active = Column(Boolean, nullable=False, default=True)

    contact = relationship(Contact, backref="addresses", foreign_keys=[contact_id])
    residents = relationship(
        Contact, backref="address", foreign_keys=[Contact.lives_at]
    )


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

    def view_guard(self, user):
        try:
            trusted_user(user)
        except:
            return False

        try:
            user_has_role(user, "global.admin")
        except:
            if user.id != self.contact_id:
                return False

    def __schema__(self):
        return Schema(
            self,
            ["consent_id", "group", "code", "wording"],
        )


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
    contact = relationship(
        Contact,
        backref=backref("notes", order_by="desc(Note._created_on)"),
        foreign_keys=[contact_id],
    )
    added_by = relationship(
        Contact, backref="notes_created", foreign_keys=[_created_by]
    )

    def view_guard(self, user):
        try:
            trusted_user(user)
        except:
            return False

        try:
            user_has_role(user, "global.admin")
        except:
            if user.id == self.contact_id or user.id != self._created_by:
                return False

    def __schema__(self):
        return Schema(
            self,
            ["id", "content"],
            custom_fields={
                "added_by": self.added_by.name,
                "date": self._created_on.isoformat(),
            },
        )


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

    def view_guard(self, user):
        try:
            trusted_user(user)
            user_has_role(user, "global.admin")
        except:
            return False

    @property
    def __schema__(self):
        return Schema(self, ["name"])


class Availability(Model):
    __tablename__ = "contact_availability"

    class AvailabilityStatuses(Enum):
        AVAILABLE = 1
        OFFLINE = 0
        EMAR = 999  # EMergency Assistance Req.
        ASSIGNED = 2
        BUSY = 3
        ON_BREAK = 4

    AVS = AvailabilityStatuses

    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    start_time = Column(DateTime, default=func.now(), primary_key=True)
    status = Column(EnumColumn(AvailabilityStatuses), nullable=False)
    latitude = Column(Float(precision=8, decimal_return_scale=7), nullable=True)
    longitude = Column(Float(precision=8, decimal_return_scale=7), nullable=True)

    contact = relationship(
        Contact, backref=backref("statuses", order_by=start_time.desc())
    )
