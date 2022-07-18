from datetime import datetime, timedelta
from enum import Enum
from model.Schema import Schema

# import services.organisation
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy import Enum as EnumColumn
from sqlalchemy.orm import relationship

from model import Model
from services.permissions import trusted_user, RoleTypes


class Branch(Model):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    abbreviation = Column(String(2), nullable=False, unique=True)

    def view_guard(self, user):
        try:
            trusted_user(user)
        except:
            return False

    def __schema__(self):
        pcds = []
        for a in self.areas:
            pcds.append(a.postcode)
        return Schema(
            self,
            [
                "id",
                "abbreviation",
                "name",
                "officers",
                "formal_name",
                "officers",
            ],
            custom_fields={"postcodes": pcds, "members": len(self.contacts)},
        )

    @property
    def formal_name(self):
        return f"{self.id}/{self.abbreviation} ({self.name}) Branch".upper()


class BranchArea(Model):

    __tablename__ = "branch_areas"

    id = Column(Integer, primary_key=True)
    branch_id = Column(
        Integer, ForeignKey("branches.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    postcode = Column(String(8), nullable=False)

    branch = relationship(Branch, backref="areas")

    addresses = relationship(
        "Address",
        backref="branch_areas",
        primaryjoin="Address.postcode.like(BranchArea.postcode + '%')",
        foreign_keys="Address.postcode",
        viewonly=True,
    )

    def view_guard(self, user):
        return True

    def __schema__(self):
        return Schema(
            self,
            ["branch_id", "postcode"],
        )


class Committee(Model):

    __tablename__ = "committees"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    abbreviation = Column(String(2), nullable=False, unique=True)
    access_level = Column(Integer, nullable=False, default=0)

    def view_guard(self, user):
        try:
            trusted_user(user)
        except:
            return False

    def __schema__(self):
        return Schema(self, ["id", "abbreviation", "name", "members"])


class Role(Model):

    __tablename__ = "roles"

    class UnitTypes(Enum):
        COMMITTEE = "committee"
        BRANCH = "branch"

    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    title = Column(String, nullable=False)
    type = Column(EnumColumn(RoleTypes), nullable=False)

    unit_type = Column(EnumColumn(UnitTypes), nullable=False)
    branch_id = Column(
        Integer,
        ForeignKey("branches.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    committee_id = Column(
        Integer,
        ForeignKey("committees.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    held_since = Column(Date, default=datetime.now())
    ends_on = Column(Date, default=datetime.now() + timedelta(weeks=52))

    branch = relationship(Branch, backref="officers")
    committee = relationship(Committee, backref="members")
    contact = relationship("Contact", backref="positions")

    @property
    def unit(self):
        if self.unit_type is self.UnitTypes.BRANCH:
            return self.branch

        return self.committee

    def view_guard(self, user):
        try:
            trusted_user(user)
        except:
            return False

    def __schema__(self):
        return Schema(
            self,
            ["id", "title"],
            custom_fields={
                "contact": {"id": self.contact.id, "name": self.contact.name},
                "held_since": self.held_since.isoformat(),
                "ends_on": self.ends_on.isoformat(),
                "unit": {
                    "name": self.unit.name,
                    "id": self.unit.id,
                    "type": self.unit_type.value,
                },
            },
        )
