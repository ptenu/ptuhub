from model.Address import Address, AddressNote, Boundary, Postcode, Street, SurveyReturn
from model.Contact import ContactAddress
from sqlalchemy.sql.expression import func

from model import db


class StreetSchema:
    def __init__(self, street: Street) -> None:
        self.street = street

    @property
    def simple(self):
        return {
            "ursn": self.street.usrn,
            "name": self.street.description,
            "addresses": len(self.street.addresses),
        }

    def extended(self, addr_list):
        return {
            "ursn": self.street.usrn,
            "name": self.street.description,
            "town": self.street.town,
            "locality": self.street.locality,
            "admin_area": self.street.admin_area,
            "addresses": addr_list,
        }

    @staticmethod
    def map_simple(street: Street):
        return StreetSchema(street).simple


class AddressSchema:
    def __init__(self, address: Address):
        self.address = address

    @property
    def simple(self):
        return {
            "uprn": self.address.uprn,
            "address": str(self.address),
            "classification": list(self.address.classification),
        }

    @property
    def simple_with_last_contact(self):
        last_return = (
            db.query(SurveyReturn)
            .filter(SurveyReturn.uprn == self.address.uprn)
            .order_by(SurveyReturn.date.desc())
            .first()
        )
        return {
            "uprn": self.address.uprn,
            "address": str(self.address),
            "classification": list(self.address.classification),
            "coordinates": [self.address.latitude, self.address.longitude],
            "last_contact": self.__map_returns(last_return),
        }

    @staticmethod
    def map_simple(address: Address):
        return AddressSchema(address).simple

    @staticmethod
    def map_with_contact(address: Address):
        return AddressSchema(address).simple_with_last_contact

    @property
    def extended(self):
        return {
            "uprn": self.address.uprn,
            "address": self.address.multiline,
            "classification": list(self.address.classification),
            "coordinates": (self.address.latitude, self.address.longitude),
            "multi_occupancy": self.address.multi_occupancy,
            "street": StreetSchema(self.address.street).simple,
            "postcode": self.address.postcode,
            "contacts": list(map(self.__map_related_contacts, self.address.contacts)),
            "boundaries": list(
                map(self.__map_boundaries, filter(None, self.address.postcode_details))
            ),
        }

    @property
    def notes(self):
        return list(map(self.__map_notes, self.address.notes))

    @property
    def returns(self):
        return list(map(self.__map_returns, self.address.survey_returns))

    def __map_returns(self, response: SurveyReturn):
        if response is None:
            return None
        rs = {}
        if response.tenure is not None:
            rs[response.QUESTIONS["tenure"]] = response.tenure.name
        else:
            rs[response.QUESTIONS["tenure"]] = None
        rs[response.QUESTIONS["response_2"]] = response.response_2
        rs[response.QUESTIONS["response_3"]] = response.response_3
        rs[response.QUESTIONS["response_4"]] = response.response_4

        return {
            "date": response.date.isoformat(),
            "added_by": {"id": response.added_by.id, "name": response.added_by.name},
            "answered": response.answered,
            "responses": rs,
        }

    def __map_notes(self, note: AddressNote):
        return {
            "id": note.id,
            "date": note.date.isoformat(),
            "added_by": {"id": note.added_by.id, "name": note.added_by.name},
            "body": note.body,
            "internal": note.internal,
            "withdrawn": note.withdrawn,
        }

    def __map_boundaries(self, boundary: Boundary):
        return {"name": boundary.name, "type": boundary.type}

    def __map_related_contacts(self, contact: ContactAddress):
        if contact.active:
            return {
                "id": contact.contact_id,
                "name": contact.contact.name,
                "relation": contact.tenure.value,
            }
