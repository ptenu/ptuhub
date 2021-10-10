from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from model import Model


class Contact(Model):

    __table__ = "contacts"

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())

    # Main Fields
    id = Column(Integer(10), primary_key=True, index=True)
    given_name = Column(String(255))
    family_name = Column(String(255))
    other_names = Column(String(255))
    first_language = Column(String(20))
    pronouns = Column(String(10))
    date_of_birth = Column(Date)

    # Membership
    membership_number = Column(String(15))
    joined_on = Column(Date)
    membership_type = Column(String(1))


class EmailAddress(Model):

    __tablename__ = "contact_emails"

    # Main
    address = Column(String(1024), primary_key=True)
    contact_id = Column(
        Integer(10), ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    verified = Column(Boolean, default=False, nullable=False)
    blocked = Column(Boolean, nullable=False, default=False)

    # Relationships
    contact = relationship(Contact, backref="email_addresses")

    @property
    def is_internal(self):
        domain = str(self.address).split("@")[1]
        return domain == "peterboroughtenants.org"


class TelephoneNumber(Model):

    __tablename__ = "contact_numbers"

    # Main
    number = Column(String(15), primary_key=True)
    contact_id = Column(
        Integer(10), ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    verified = Column(Boolean, default=False, nullable=False)
    blocked = Column(Boolean, nullable=False, default=False)

    # Relationships
    contact = relationship(Contact, backref="phone_numbers")


class ContactAddress(Model):

    __tablename__ = "contact_addresses"

    id = Column(Integer(10), primary_key=True, index=True)
    contact_id = Column(
        Integer(10), ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    uprn = Column(String(15))
    custom_address = Column(Text)

    # Relation to contact
    owner_from = Column(Date)
    owner_until = Column(Date)
    occupier_from = Column(Date)
    occupier_until = Column(Date)
    tenant_from = Column(Date)
    tenant_until = Column(Date)

    # Table relation
    # Relationships
    contact = relationship(Contact, backref="addresses")

    @property
    def active(self):
        if self.owner_from is not None:
            if self.owner_until is None or self.owner_until > datetime.today():
                return True

        if self.occupier_from is not None:
            if self.occupier_until is None or self.occupier_until > datetime.today():
                return True

        if self.tenant_from is not None:
            if self.tenant_until is None or self.tenant_until > datetime.today():
                return True

        return None


class Consent(Model):

    __table__ = "consents"

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())

    # Main
    contact_id = Column(
        Integer(10),
        ForeignKey("contacts.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    consent_id = Column(Integer(3), primary_key=True, autoincrement=True)
    group = Column(String(25), nullable=False)
    code = Column(String(25), nullable=False)
    source = Column(String(25))
    expires = Column(Date)
    wording = Column(Text)

    # Relationships
    contact = relationship(Contact, backref="consents")
