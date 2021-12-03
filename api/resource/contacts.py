from typing import List, Optional

import api.middleware.authentication as auth
import falcon
from api.interface.contacts import ContactInterface
from falcon import HTTP_201, HTTP_204, HTTP_200
from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    address: Optional[EmailStr] = None
    blocked: bool
    verified: bool

    class Config:
        orm_mode = True


class TelSchema(BaseModel):
    number: Optional[str] = None
    blocked: bool
    verified: bool

    class Config:
        orm_mode = True


class ContactSchema(BaseModel):
    id: Optional[int] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    other_names: Optional[str] = None
    email: Optional[EmailSchema] = None
    telephone: Optional[TelSchema] = None
    first_language: Optional[str] = None
    pronouns: Optional[str] = None

    class Config:
        orm_mode = True


class ContactList(BaseModel):

    contacts: List[ContactSchema] = []

    class Config:
        orm_mode = True


class ContactsResource:
    @falcon.before(auth.EnforceRoles, ["contacts.manage", "contacts.view"])
    def on_get_collection(self, req, resp):
        """
        Get a list of contacts
        """
        contacts_interface = ContactInterface(self.session)

        contacts = contacts_interface.get_all_contacts()
        m = ContactList().parse_obj({"contacts": contacts})
        resp.text = m.json()

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

        parsed_body = ContactSchema().parse_obj(contact)

        new_contact = ContactInterface(self.session).create_new_contact(parsed_body)

        resp.text = ContactSchema().from_orm(new_contact).json()
        resp.status = HTTP_201

    @falcon.before(auth.EnforceRoles, ["contacts.manage", "contacts.view"])
    def on_get_single(self, req, resp, id):
        """
        Return a single contact
        """

        contacts_interface = ContactInterface(self.session)
        contact = contacts_interface.get_contact(id)
        contact = ContactSchema().from_orm(contact)
        resp.text = contact.json()

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
        parsed_body = ContactSchema().parse_obj(contact)

        updated_contact = contacts_interface.update_contact(id, parsed_body)
        resp.text = ContactSchema().from_orm(updated_contact).json()
        resp.status = HTTP_200

    @falcon.before(auth.EnforceRoles, ["global.admin"])
    def on_delete_single(self, req, resp, id):
        """
        Delete a specified contact
        """
        contacts_interface = ContactInterface(self.session)
        contacts_interface.delete_contact(id)
        resp.status = HTTP_204
