from datetime import datetime, timedelta
from enum import Enum

from services.organisation import get_branch_members
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy import Enum as EnumColumn
from sqlalchemy.orm import relationship

from model import Model


class RoleTypes(Enum):
    CHAIR = "chair"
    SEC = "secretary"
    TRES = "treasurer"
    TRUST = "trustee"
    MEM = "member"
    DEL = "delegate"
    REP = "representative"
    SREP = "senior representative"
    ORG = "organiser"
    LREP = "learning rep"


class Branch(Model):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    abbreviation = Column(String(2), nullable=False, unique=True)

    @property
    def members(self):
        return get_branch_members(self)


class BranchArea(Model):

    __tablename__ = "branch_areas"

    id = Column(Integer, primary_key=True)
    branch_id = Column(
        Integer, ForeignKey("branches.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    postcode = Column(String(8), nullable=False)

    branch = relationship(Branch, backref="areas")


class Committee(Model):

    __tablename__ = "committees"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    abbreviation = Column(String(2), nullable=False, unique=True)


class Roles(Model):

    __tablename__ = "roles"

    class UnitTypes(Enum):
        COMMITTEE = "committee"
        BRANCH = "branch"

    id = Column(Integer, primary_key=True)
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    title = Column(String, nullable=False)
    type = Column(EnumColumn(RoleTypes), nullable=False)
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
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
    role_title = Column(String(255), nullable=True)
    held_since = Column(Date, default=datetime.now())
    ends_on = Column(Date, default=datetime.now() + timedelta(weeks=52))

    branch = relationship(Branch, backref="officers")
    committee = relationship(Committee, backref="members")
    contact = relationship("Contact", backref="branches")
