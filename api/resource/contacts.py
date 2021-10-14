import falcon
import json
from api.interface.contacts import ContactInterface


class ContactsCollection:
    def on_get(self, req, resp):
        """
        Get a list of contacts
        """
        contacts_interface = ContactInterface()

        resp.text = json.dumps(contacts_interface.get_all_contacts())

    def on_post(self, req, resp):
        """
        Create a new contact
        """

        # Get paramaters from body
        body = req.get_media(default_when_empty=None)

        if body is None:
            raise falcon.HTTPBadRequest(description="Empty body")

        if "contact" not in body:
            raise falcon.HTTPBadRequest(
                description="Body must contain a person element."
            )

        contact = body.contact

        new_contact = ContactInterface.create_new_contact(contact)
