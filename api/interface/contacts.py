from model import Session as db
from model.Contact import Contact


class ContactInterface:
    def get_all_contacts(self):
        """
        Return list containing all contacts
        """

        contacts = db.query(Contact).all()

        return contacts

    def create_new_contact(self, contact):
        """
        Create a new contact
        """

        new_contact = Contact()

        for key in contact:
            if hasattr(new_contact, key):
                setattr(new_contact, key, contact[key])

        db.commit()

        return new_contact
