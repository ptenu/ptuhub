from datetime import datetime
from model.Contact import Contact, ContactAddress, EmailAddress, TelephoneNumber
from api.schemas.address import AddressSchema


def dateOr(value: datetime, default):
    if value is not None:
        return value.isoformat()

    return default


class ContactSchema:
    def __init__(self, contact: Contact) -> None:
        self.contact = contact

    @property
    def simple(self):
        output = {
            "id": self.contact.id,
            "name": self.contact.name,
            "avatar_url": None,
        }

        if self.contact.avatar is not None:
            output["avatar_url"] = self.contact.avatar.public_url

        return output

    @property
    def extended(self):
        output = {
            "id": self.contact.id,
            "name": self.contact.name,
            "legal_name": self.contact.legal_name,
            "date_of_birth": dateOr(self.contact.date_of_birth, None),
            "joined_on": dateOr(self.contact.joined_on, None),
            "avatar_url": None,
            "membership_type": self.contact.membership_type,
            "membership_number": self.contact.membership_number,
            "created": dateOr(self.contact._created_on, None),
            "updated": dateOr(self.contact._updated_on, None),
            "account_blocked": self.contact.account_blocked,
            "addresses": list(
                map(self.__map_addresses, self.contact.address_relations)
            ),
            "email_addresses": list(
                map(self.__map_emails, self.contact.email_addresses)
            ),
            "telephone_numbers": list(
                map(self.__map_telephone, self.contact.phone_numbers)
            ),
        }

        if self.contact.avatar is not None:
            output["avatar_url"] = self.contact.avatar.public_url

        return output

    @staticmethod
    def map_simple(contact: Contact):
        return ContactSchema(contact).simple

    def __map_addresses(self, ca: ContactAddress):
        output = {"mail_to": ca.mail_to, "active": ca.active}

        if ca.custom_address is not None:
            output["address"] = ca.custom_address

        if ca.uprn is not None:
            output["address"] = AddressSchema(ca.address).simple

        return output

    def __map_emails(self, email: EmailAddress):
        return {
            "address": email.address.lower(),
            "prefered": self.contact.prefered_email == email.address,
        }

    def __map_telephone(self, tel: TelephoneNumber):
        return {
            "number": tel.number,
            "prefered": self.contact.prefered_phone == tel.number,
            "description": tel.description,
        }
