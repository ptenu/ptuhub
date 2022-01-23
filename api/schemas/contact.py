from datetime import datetime
from model.Contact import Contact


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
            "email": self.contact.prefered_email,
            "telephone": self.contact.prefered_phone,
        }

        if self.contact.avatar is not None:
            output["avatar_url"] = self.contact.avatar.public_url

        return output

    @staticmethod
    def map_simple(contact: Contact):
        return ContactSchema(contact).simple
