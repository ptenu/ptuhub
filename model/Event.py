from enum import Enum

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Time
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from model import Model
from model import db


class EventTypes(Enum):
    MEETING = "meeting"
    ER = "eviction resistance"
    CLASS = "training session"
    PUB = "public event"
    PREP = "briefing"
    SOC = "social"
    MS = "member support"
    POL = "political"
    OTHER = "other"


class Attendable(Model):
    """
    An event, meeting, protest etc... anything which can be attended
    """

    __tablename__ = "attendables"

    class Periods(Enum):
        DAYS = 1
        WEEKS = 7
        MONTHS = 31
        YEARS = 365

        NTH_WEEK_OF_MONTH = 100  # i.e. 3rd Tuesday of each month
        DAY_OF_MONTH = 200  # i.e. 27th of Each month
        NTH_MONTH_OF_YEAR = 300  # specific month each year, on same day

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    uprn = Column(
        BigInteger, ForeignKey("addresses.uprn", ondelete="SET NULL"), nullable=True
    )
    location = Column(Text, nullable=True)
    capacity = Column(Integer)
    type = Column(EnumColumn(EventTypes), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=True)
    first_occurance = Column(Date, nullable=False)
    last_occurance = Column(Date, nullable=True)
    frequency = Column(Integer, nullable=False)
    period = Column(EnumColumn(Periods), nullable=False)


class Rsvp(Model):

    __tablename__ = "rsvp_list"

    class Responses(Enum):
        OKAY = "attending"
        NA = "not attending"

    event_id = Column(
        Integer, ForeignKey("attendables.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    occurance = Column(Integer, nullable=False, default=0)
    response = Column(EnumColumn(Responses), nullable=False)

    event = relationship(Attendable, backref="responses")
