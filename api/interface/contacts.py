from falcon.errors import HTTPNotFound
from model import Session
from model.File import File
from model.Contact import Contact


class ContactInterface:
    def __init__(self, session: Session):
        self.db = session

    def get_all_contacts(self):
        """
        Return list containing all contacts
        """

        contacts = self.db.query(Contact).all()

        return contacts

    def get_contact(self, id):
        """
        Get a single contact
        """

        contact = self.db.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        return contact

    def create_new_contact(self, contact):
        """
        Create a new contact
        """

        contact = contact.dict(exclude_unset=True)

        new_contact = Contact()
        self.db.add(new_contact)

        for key in contact:
            setattr(new_contact, key, contact[key])

        self.db.commit()

        return new_contact

    def update_contact(self, id, fields):
        """
        Perform a partial update on a contact
        """

        fields = fields.dict(exclude_unset=True)

        contact = self.db.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        for key in fields:
            setattr(contact, key, fields[key])

        self.db.commit()

        return contact

    def delete_contact(self, id):
        """
        Delete a contact
        """

        contact = self.db.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        self.db.delete(contact)
        self.db.commit()

        return
