from enum import Enum

from sqlalchemy import BigInteger, Boolean, Column, Date
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from model import Model
from model import Session as db


class Address(Model):
    __tablename__ = "addresses"

    uprn = Column(BigInteger, primary_key=True)
    usrn = Column(
        BigInteger,
        ForeignKey("streets.usrn", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    parent_uprn = Column(BigInteger, ForeignKey("addresses.uprn", ondelete="CASCADE"))
    state = Column(Integer)
    parent_uprn = Column(BigInteger, ForeignKey("addresses.uprn", ondelete="CASCADE"))

    # This is how legal addresses are numbered
    # For more information look for the OS AddressBase Documentation.

    # SAO = Secondary addressable object (e.g. First Floor, Flat A)
    sao_start_number = Column(Integer, nullable=True)
    sao_start_suffix = Column(String(2), nullable=True)
    sao_end_number = Column(Integer, nullable=True)
    sao_end_suffix = Column(String(2), nullable=True)
    sao_text = Column(String(90), nullable=True)

    # PAO = Primary Addressable Object (i.e. the door number)
    pao_start_number = Column(Integer, nullable=True)
    pao_start_suffix = Column(String(2), nullable=True)
    pao_end_number = Column(Integer, nullable=True)
    pao_end_suffix = Column(String(2), nullable=True)
    pao_text = Column(String(90), nullable=True)

    postcode = Column(String(8), ForeignKey("postcodes.pcds", ondelete="CASCADE"))

    area_name = Column(String(40), nullable=True)
    level = Column(String(30), nullable=True)

    multi_occupancy = Column(Integer, nullable=True)
    latitude = Column(Float(precision=8, decimal_return_scale=7), nullable=True)
    longitude = Column(Float(precision=8, decimal_return_scale=7), nullable=True)
    classification_code = Column(
        String(length=6), ForeignKey("classifications.code", ondelete="CASCADE")
    )

    # Relationships
    contacts = relationship("ContactAddress", backref="address")
    street = relationship("Street", back_populates="addresses", cascade="all")
    parent = relationship("Address", remote_side=[uprn], back_populates="sub_addresses")
    sub_addresses = relationship(
        "Address", remote_side=[parent_uprn], back_populates="parent"
    )
    classification = relationship("Classification", back_populates="addresses")

    def __init__(self, uprn):
        self.uprn = uprn

    @property
    def sao_str(self):
        sao = ""

        if self.sao_text is not None:
            sao += self.sao_text

        if self.sao_start_number is not None:
            if sao != "":
                sao += ", "
            sao += str(self.sao_start_number)

        if self.sao_start_suffix is not None:
            sao += self.sao_start_suffix

        if self.sao_end_number is not None:
            sao += f"-{str(self.sao_end_number)}"

        if self.sao_end_suffix is not None:
            sao += self.sao_end_suffix

        return sao

    @property
    def pao_str(self):
        pao = ""

        if self.pao_text is not None:
            pao += self.pao_text

        if self.pao_start_number is not None:
            if pao != "":
                pao += ", "
            pao += str(self.pao_start_number)

        if self.pao_start_suffix is not None:
            pao += self.pao_start_suffix

        if self.pao_end_number is not None:
            pao += f"-{str(self.pao_end_number)}"

        if self.pao_end_suffix is not None:
            pao += self.pao_end_suffix

        return pao

    def __str__(self):
        single_line = ""

        if self.sao_str != "":
            single_line = f"{self.sao_str}, "

        single_line += self.pao_str

        if self.pao_start_number is None or self.pao_start_number == "":
            single_line += ","

        single_line += " " + self.street.description

        if self.street.locality is not None:
            single_line = f"{single_line}, {self.street.locality}"

        return f"{single_line}, {self.street.town}, {self.postcode}"

    @property
    def single_line(self):
        return self.__str__()

    @property
    def multiline(self):
        address = []

        if self.sao_str != "":
            address.append(self.sao_str)

        if self.pao_start_number is not None and self.pao_start_number != "":
            address.append(f"{self.pao_str} {self.street}")
        else:
            address.append(self.pao_text)
            address.append(str(self.street))

        if self.street.locality is not None:
            address.append(self.street.locality)

        address.append(self.street.town)

        if self.street.town != self.street.admin_area:
            address.append(self.street.admin_area)

        address.append(self.postcode)

        return address


class Street(Model):
    __tablename__ = "streets"

    STATES = {1: "Under Construction", 2: "Open", 4: "DELETE"}
    CLASSIFICATIONS = {
        4: "Pedestrian way or footpath",
        6: "Cycletrack or cycleway",
        8: "All vehicles",
        9: "Restricted byway",
        10: "Bridleway",
    }
    SURFACES = {1: "Metalled (Paved)", 2: "Un-metalled (Gravel)", 3: "Mixed"}

    usrn = Column(BigInteger, primary_key=True)
    state_code = Column(Integer, nullable=True)
    surface_code = Column(Integer, nullable=True)
    classification_code = Column(Integer, nullable=True)
    description = Column(String(100))
    locality = Column(String(35))
    town = Column(String(30))
    admin_area = Column(String(30), nullable=True)

    addresses = relationship(
        Address, back_populates="street", cascade="all, delete-orphan"
    )

    def __init__(self, usrn):
        self.usrn = usrn

    def __str__(self):
        return self.description.upper()


class Classification(Model):
    __tablename__ = "classifications"

    code = Column(String(6), primary_key=True)
    class_desc = Column(String(200), nullable=True)
    primary_code = Column(String(1), nullable=True)
    secondary_code = Column(String(1), nullable=True)
    tertiary_code = Column(Integer, nullable=True)
    quaternary_code = Column(String(2), nullable=True)

    primary_desc = Column(String(200), nullable=True)
    secondary_desc = Column(String(200), nullable=True)
    tertiary_desc = Column(String(200), nullable=True)
    quaternary_desc = Column(String(200), nullable=True)

    addresses = relationship(
        Address, back_populates="classification", cascade="all, delete-orphan"
    )

    def __init__(self, code):
        self.code = code

    def __str__(self):
        return self.class_desc

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        self.i += 1

        if self.i == 0:
            if self.primary_desc is not None:
                return self.primary_desc
        if self.i == 1:
            if self.secondary_desc is not None:
                return self.secondary_desc
        if self.i == 2:
            if self.tertiary_desc is not None:
                return self.tertiary_desc
        if self.i == 3:
            if self.quaternary_desc is not None:
                return self.quaternary_desc

        raise StopIteration


class Boundary(Model):
    __tablename__ = "boundaries"

    TYPES = {
        "E05": "Ward",
        "E06": "Unitary Authority",
        "E07": "District Council",
        "E10": "County Council",
        "E14": "Constituency",
        "E47": "Combined Authority",
        "E58": "County Electoral Division",
    }

    code = Column(String(9), primary_key=True)
    name = Column(String(200))

    def __init__(self, code, name):
        self.code = code
        self.name = name

    def __str__(self):
        return f"{self.name} ({self.type})"

    @property
    def type(self):
        return self.TYPES[self.code[:3]]


class Postcode(Model):
    __tablename__ = "postcodes"

    pcds = Column(String(8), primary_key=True)
    e05 = Column(String(9))
    e06 = Column(String(9))
    e07 = Column(String(9))
    e10 = Column(String(9))
    e14 = Column(String(9))
    e47 = Column(String(9))
    e58 = Column(String(9))

    addresses = relationship(Address, backref="postcode_details")

    def __init__(self, postcode):
        self.pcds = postcode

    def add_code(self, code):
        tc = code[:3]
        if tc == "E99":
            return

        if tc not in Boundary.TYPES.keys():
            return

        setattr(self, tc.lower(), code)

    def __str__(self):
        return self.pcds

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        codes = (
            "e05",
            "e06",
            "e07",
            "e10",
            "e14",
            "e47",
            "e58",
        )
        if self.i > len(codes) - 1:
            raise StopIteration

        c_type = codes[self.i]
        self.i += 1
        if hasattr(self, c_type):
            c_full = getattr(self, c_type)
        else:
            return None

        bdry = db.query(Boundary).get(c_full)
        return bdry


class AddressNote(Model):
    __tablename__ = "address_notes"

    id = Column(Integer, primary_key=True)
    uprn = Column(BigInteger, ForeignKey("addresses.uprn", ondelete="CASCADE"))
    date = Column(Date)
    body = Column(Text, nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"))
    internal = Column(Boolean, default=True, nullable=False)
    withdrawn = Column(Boolean, default=False, nullable=False)
    sensitive = Column(Boolean, default=False, nullable=False)

    address = relationship("Address", backref="notes")
    added_by = relationship("Contact", backref="address_notes")


class SurveyReturn(Model):
    __tablename__ = "survey_returns"

    class TenureTypes(Enum):
        PRIVATE_RENT = "P"
        SOCIAL_RENT = "S"
        LICENSEE = "L"
        OWNER_OCCUPIER = "O"
        HMO = "H"
        OTHER = "U"

    id = Column(Integer, primary_key=True)
    uprn = Column(BigInteger, ForeignKey("addresses.uprn", ondelete="CASCADE"))
    date = Column(Date)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"))
    tenure = Column(EnumColumn(TenureTypes, name="survey_tenure_types"), nullable=True)
    housing_cost = Column(Integer, nullable=True)
    answered = Column(Boolean, nullable=False, default=True)

    address = relationship("Address", backref="survey_returns")
    added_by = relationship("Contact", backref="survey_returns")
