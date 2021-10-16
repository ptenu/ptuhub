import falcon
from falcon import HTTP_204, HTTP_201
from api.interface.contacts import ContactInterface
from pydantic import BaseModel, EmailStr
from typing import List, Optional


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


class ContactsCollection:
    def on_get(self, req, resp):
        """
        Get a list of contacts
        """
        contacts_interface = ContactInterface()

        contacts = contacts_interface.get_all_contacts()
        m = ContactList().parse_obj({"contacts": contacts})
        resp.text = m.json()

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

        contact = body["contact"]

        parsed_body = ContactSchema().parse_obj(contact)

        new_contact = ContactInterface().create_new_contact(parsed_body)

        resp.text = ContactSchema().from_orm(new_contact).json()
        resp.status = HTTP_201


class ContactCollection:
    def on_get(self, req, resp, id):
        contacts_interface = ContactInterface()
        contact = contacts_interface.get_contact(id)
        contact = ContactSchema().from_orm(contact)
        resp.text = contact.json()

    def on_patch(self, req, resp, id):
        contacts_interface = ContactInterface()

    def on_delete(self, req, resp, id):
        contacts_interface = ContactInterface()
        contacts_interface.delete_contact(id)
        resp.status = HTTP_204
