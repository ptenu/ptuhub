from typing import List, Optional

from falcon.errors import HTTPBadRequest

import api.middleware.authentication as auth
import falcon
from api.interface.contacts import ContactInterface
from falcon import HTTP_201, HTTP_204, HTTP_200
import json


class ContactsResource:
    @falcon.before(auth.EnforceRoles, ["contacts.manage", "contacts.view"])
    def on_get_collection(self, req, resp):
        """
        Get a list of contacts
        """
        contacts_interface = ContactInterface(self.session)

        contacts = contacts_interface.get_all_contacts()

        contacts_mapped = []
        for c in contacts:
            contacts_mapped.append(c.dict)

        resp.text = json.dumps({"contacts": contacts_mapped})

    def on_post_collection(self, req, resp):
        """
        Create a new contact
        """

        # Get paramaters from body
        body = req.get_media(default_when_empty=None)

        if body is None:
            raise falcon.HTTPBadRequest(description="Empty body")

        if "contact" not in body:
            raise falcon.HTTPBadRequest(
                description="Body must contain a contact element."
            )

        contact = body["contact"]
        new_contact = ContactInterface(self.session).create_new_contact(contact)

        resp.text = json.dumps(new_contact.dict)
        resp.status = HTTP_201

    @falcon.before(auth.EnforceRoles, ["contacts.manage", "contacts.view"])
    def on_get_single(self, req, resp, id):
        """
        Return a single contact
        """

        contacts_interface = ContactInterface(self.session)
        contact = contacts_interface.get_contact(id)
        resp.text = json.dumps(contact.dict_ext)

    @falcon.before(auth.EnforceRoles, ["contacts.manage"])
    def on_patch_single(self, req, resp, id):
        """
        Update specified fields on a contact
        """

        body = req.get_media(default_when_empty=None)

        if body is None:
            raise falcon.HTTPBadRequest(description="Empty body")

        if "contact" not in body:
            raise falcon.HTTPBadRequest(
                description="Body must contain a person element."
            )

        contacts_interface = ContactInterface(self.session)

        contact = body["contact"]

        updated_contact = contacts_interface.update_contact(id, contact)
        resp.text = json.dumps(updated_contact.dict_ext)
        resp.status = HTTP_200

    @falcon.before(auth.EnforceRoles, ["global.admin"])
    def on_delete_single(self, req, resp, id):
        """
        Delete a specified contact
        """
        contacts_interface = ContactInterface(self.session)
        contacts_interface.delete_contact(id)
        resp.status = HTTP_204


class AvatarResource:
    @falcon.before(auth.EnforceRoles, ["contacts.manage"])
    def on_put(self, req, resp, contact_id):

        form = req.get_media()
        image = None
        for part in form:
            if part.name == "avatar":
                image = part

        if image is None:
            raise HTTPBadRequest(
                "Missing parameter",
                "Please include an image you wish to use as an avatar",
            )

        contacts_interface = ContactInterface(self.session)
        contacts_interface.put_avatar(contact_id, image)
