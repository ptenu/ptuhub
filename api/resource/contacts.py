import json
import tempfile

import api.middleware.authentication as auth
import falcon
from api.interface.contacts import ContactInterface
from falcon import HTTP_201, HTTP_204
from falcon.errors import HTTPBadRequest, HTTPNotFound
from api.schemas.contact import ContactSchema
from model.Contact import Contact, EmailAddress, TelephoneNumber
from services.email import EmailService
from services.sms import SmsService


class ContactsResource:
    @falcon.before(auth.EnforceRoles, ["officer", "rep", "organiser"])
    def on_get_collection(self, req, resp):
        """
        Get a list of contacts
        """
        contacts = (
            self.session.query(Contact).order_by(Contact._created_on.desc()).all()
        )

        result = list(map(ContactSchema.map_simple, contacts))
        resp.text = json.dumps(result)

    def on_post_collection(self, req, resp):
        """
        Create a new contact
        """

        # Get paramaters from body
        body = req.get_media()

        new_contact = ContactInterface(self.session).create_new_contact(body)
        schema = ContactSchema(new_contact)

        resp.text = json.dumps(schema.extended)

    @falcon.before(auth.EnforceRoles, ["officer", "rep", "organiser"])
    def on_get_single(self, req, resp, id):
        """
        Return a single contact
        """

        contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        schema = ContactSchema(contact)
        resp.text = json.dumps(schema.extended)

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_patch_single(self, req, resp, id):
        """
        Update specified fields on a contact
        """

        body = req.get_media()
        contacts_interface = ContactInterface(self.session)

        updated_contact = contacts_interface.update_contact(id, body)
        schema = ContactSchema(updated_contact)

        resp.text = json.dumps(schema.extended)

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_delete_single(self, req, resp, id):
        """
        Delete a specified contact
        """
        contacts_interface = ContactInterface(self.session)
        contacts_interface.delete_contact(id)
        resp.status = HTTP_204

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_post_email(self, req, resp, id):
        """
        Create or update a contact email address
        """

        body = req.get_media()
        needs_verification = False

        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")

        if "address" not in body:
            raise HTTPBadRequest(description="You must include an address field.")

        email = self.session.query(EmailAddress).get(body["address"])
        if email is None:
            needs_verification = True

            email = EmailAddress(contact, body["address"])
            if contact.id != req.context.user.id:
                needs_verification = False
                email.verified = True
            else:
                EmailService().send_verification(email.address)

            self.session.add(email)

        if "prefered" in body:
            if body["prefered"] not in (True, False):
                raise HTTPBadRequest(description="prefered must be true or false")

            contact.email = email

        self.session.commit()

        resp.text = json.dumps({"verification": needs_verification})

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_post_sms(self, req, resp, id):
        """
        Create or update a contact telephone number
        """

        body = req.get_media()
        needs_verification = False

        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")

        if "number" not in body:
            raise HTTPBadRequest(description="You must include a number field.")

        number = self.session.query(TelephoneNumber).get(body["number"])
        if number is None:
            needs_verification = True

            number = TelephoneNumber(body["number"])
            number.contact = contact

            if contact.id != req.context.user.id or not number.number.startswith("07"):
                number.verified = True
                needs_verification = False
            else:
                SmsService(self.session).send_verification(number.number)

            self.session.add(number)

        if "prefered" in body:
            if body["prefered"] not in (True, False):
                raise HTTPBadRequest(description="prefered must be true or false")

            contact.telephone = number

        self.session.commit()

        resp.text = json.dumps({"verification": needs_verification})


class AvatarResource:
    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_put(self, req, resp, id):

        form = req.get_media()
        did_the_user_upload_an_image = False

        for part in form:
            if part.name != "avatar":
                continue

            did_the_user_upload_an_image = True

            with tempfile.TemporaryFile() as tmp_image:
                tmp_image.write(part.stream.read())
                contacts_interface = ContactInterface(self.session)
                contacts_interface.put_avatar(id, tmp_image)
                break

        if not did_the_user_upload_an_image:
            raise HTTPBadRequest(
                "Missing parameter",
                "Please include an image you wish to use as an avatar",
            )

        resp.status = HTTP_201

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_delete(self, req, resp, id):
        ci = ContactInterface(self.session)
        ci.clear_avatar(id)

        resp.status = HTTP_204
