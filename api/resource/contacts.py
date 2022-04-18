import json
import tempfile
from datetime import datetime

from api.interface.contacts import ContactInterface
from falcon import HTTP_201, HTTP_204
from falcon.errors import HTTPBadRequest, HTTPForbidden, HTTPNotFound
from model.Address import Address
from model.Contact import (
    Consent,
    Contact,
    ContactAddress,
    EmailAddress,
    Note,
    TelephoneNumber,
)
from services.email import EmailService
from services.permissions import user_has_role
from services.sms import SmsService


class ContactsResource:
    def on_get_collection(self, req, resp):
        """
        Get a list of contacts
        """
        contacts = (
            self.session.query(Contact).order_by(Contact._created_on.desc()).all()
        )

        resp.context.media = contacts
        resp.context.fields = ["id", "name"]

    def on_post_collection(self, req, resp):
        """
        Create a new contact
        """

        # Get paramaters from body
        input = req.get_media()

        new_contact = Contact()
        self.session.add(new_contact)

        try:
            if "given_name" in input:
                new_contact.given_name = str(input["given_name"]).capitalize().strip()

            if "family_name" in input:
                new_contact.family_name = str(input["family_name"]).capitalize().strip()

            if "other_names" in input:
                new_contact.other_names = str(input["other_names"]).capitalize().strip()

            if "first_language" in input:
                new_contact.first_language = input["first_language"]

            if "pronouns" in input:
                new_contact.pronouns = input["pronouns"]

            if "date_of_birth" in input:
                new_contact.date_of_birth = datetime(
                    input["date_of_birth"][0],
                    input["date_of_birth"][1],
                    input["date_of_birth"][2],
                )
        except:
            raise HTTPBadRequest

        self.session.commit()

        resp.context.media = new_contact

    def on_get_single(self, req, resp, id):
        """
        Return a single contact
        """

        contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        resp.context.media = contact

    def on_patch_single(self, req, resp, id):
        """
        Update specified fields on a contact
        """

        if req.context.user is None:
            raise HTTPForbidden

        input = req.get_media()
        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        if not contact.view_guard(req.context.user):
            raise HTTPForbidden

        try:
            if "given_name" in input:
                contact.given_name = str(input["given_name"]).capitalize().strip()

            if "family_name" in input:
                contact.family_name = str(input["family_name"]).capitalize().strip()

            if "other_names" in input:
                contact.other_names = str(input["other_names"]).capitalize().strip()

            if "first_language" in input:
                contact.first_language = input["first_language"]

            if "pronouns" in input:
                contact.pronouns = input["pronouns"]

            if "date_of_birth" in input:
                contact.date_of_birth = datetime(
                    input["date_of_birth"][0],
                    input["date_of_birth"][1],
                    input["date_of_birth"][2],
                )
        except:
            raise HTTPBadRequest

        self.session.commit()

        resp.context.media = contact

    def on_delete_single(self, req, resp, id):
        """
        Delete a specified contact
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except:
            raise HTTPForbidden

        contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        self.session.delete(contact)
        self.session.commit()
        resp.status = HTTP_204

    def on_post_email(self, req, resp, id):
        """
        Create or update a contact email address
        """

        body = req.get_media()
        needs_verification = False

        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")
        if not contact.view_guard(req.context.user):
            raise HTTPForbidden

        if "address" not in body:
            raise HTTPBadRequest(description="You must include an address field.")

        email = self.session.query(EmailAddress).get(str(body["address"]).upper())
        if email is None:
            needs_verification = True

            email = EmailAddress(contact, body["address"])
            if contact.id != req.context.user.id:
                needs_verification = False
                email.verified = True
            else:
                es = EmailService()
                es.db = self.session
                es.send_verification(email.address)

            self.session.add(email)

        if "prefered" in body:
            if body["prefered"] not in (True, False):
                raise HTTPBadRequest(description="prefered must be true or false")

            if body["prefered"] == True:
                contact.email = email
            elif contact.email.address == email.address:
                contact.email = None

        self.session.commit()

        resp.media = {"verification": needs_verification}

    def on_post_sms(self, req, resp, id):
        """
        Create or update a contact telephone number
        """

        body = req.get_media()
        needs_verification = False

        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")
        if not contact.view_guard(req.context.user):
            raise HTTPForbidden

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

            if body["prefered"] == True:
                contact.telephone = number
            elif contact.telephone.number == number.number:
                contact.telephone = None

        self.session.commit()

        resp.media = {"verification": needs_verification}

    def on_put_verify(self, req, resp):
        """
        Confirm a verification code for email or telephone no.
        """

        body = req.get_media()
        if "address" not in body and "number" not in body:
            raise HTTPBadRequest

        if "code" not in body:
            raise HTTPBadRequest

        if "address" in body:
            es = EmailService()
            es.db = self.session
            es.validate(body["address"], body["code"])

        if "number" in body:
            es = SmsService(self.session)
            es.validate(body["number"], body["code"])

        resp.status = HTTP_204

    def on_delete_sms(self, req, resp, id, number):
        """
        Delete a phone number
        """

        tel: TelephoneNumber = self.session.query(TelephoneNumber).get(number)
        if tel is None:
            raise HTTPNotFound

        if not tel.view_guard(req.context.user):
            raise HTTPForbidden

        self.session.delete(tel)
        self.session.commit()
        resp.status = HTTP_204

    def on_delete_email(self, req, resp, id, address):
        """
        Delete an email
        """

        email: EmailAddress = self.session.query(EmailAddress).get(address.upper())
        if email is None:
            raise HTTPNotFound

        if not email.view_guard(req.context.user):
            raise HTTPForbidden

        self.session.delete(email)
        self.session.commit()
        resp.status = HTTP_204

    def on_put_consent(self, req, resp, id):
        """
        Add a consent to the specified user
        """

        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")
        if not contact.view_guard(req.context.user):
            raise HTTPForbidden

        body = req.get_media()
        try:
            consent = Consent()
            self.session.add(consent)

            consent.contact = contact
            consent.group = str(body["group"]).upper().strip()
            consent.code = str(body["code"]).upper().strip()

            if "wording" in body:
                consent.wording = body["wording"]

            if "source" in body:
                consent.source = body["source"]
        except KeyError:
            raise HTTPBadRequest

        self.session.commit()
        resp.status = HTTP_201

    def on_delete_consent(self, req, resp, id, consent_id):
        """
        Remove a consent
        """

        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")
        if contact.view_guard(req.context.user) == False:
            raise HTTPForbidden

        consent: Consent = self.session.query(Consent).get([id, consent_id])
        if consent is None:
            raise HTTPNotFound

        self.session.delete(consent)
        self.session.commit()
        resp.status = HTTP_204

    def on_put_note(self, req, resp, id):
        """
        Create a note for a contact
        """
        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")
        if contact.view_guard(req.context.user) == False:
            raise HTTPForbidden

        body = req.get_media()
        note: Note = Note()
        try:
            previous_notes = (
                self.session.query(Note).where(Note.contact_id == id).count()
            )
            note.id = previous_notes + 1
            note.added_by = req.context.user
            note.contact = contact
            note.content = body["text"]
        except KeyError:
            raise HTTPBadRequest

        self.session.add(note)
        self.session.commit()

        resp.status = HTTP_201

    def on_delete_note(self, req, resp, id, note_id):
        """
        Create a note for a contact
        """
        contact: Contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")
        if contact.view_guard(req.context.user) == False:
            raise HTTPForbidden

        note: Note = self.session.query(Note).get([note_id, id])
        if note is None:
            raise HTTPNotFound(description="Note not found")
        if note.view_guard(req.context.user) == False:
            raise HTTPForbidden

        self.session.delete(note)
        self.session.commit()

        resp.status = HTTP_204


class AvatarResource:
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

    def on_delete(self, req, resp, id):
        ci = ContactInterface(self.session)
        ci.clear_avatar(id)

        resp.status = HTTP_204


class AddressResource:
    def on_put(self, req, resp, id):
        """
        Associate an address with a contact
        """

        body = req.get_media()

        if "uprn" not in body and "address" not in body:
            raise HTTPBadRequest(
                description="You must include EITHER a custom address string, or an address UPRN."
            )

        resp.status = HTTP_204

        contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound(description="Contact not found")

        if not contact.view_guard(req.context.user):
            raise HTTPForbidden

        ca = self.__get_contact_address(contact, body)
        if ca is None:
            ca = ContactAddress()
            ca.contact = contact
            self.session.add(ca)
            resp.status = HTTP_201

        if "uprn" in body:
            address: Address = self.session.query(Address).get(body["uprn"])
            if address is None:
                raise HTTPNotFound(description="Address not found")
            ca.uprn = address.uprn

        elif "address" in body:
            ca.custom_address = body["address"]

        if "tenure" not in body:
            raise HTTPBadRequest(description="You must include a tenure type.")

        try:
            tenure = str(body["tenure"]).upper()
            tenure_type = ContactAddress.Tenure[tenure]
            ca.tenure = tenure_type

        except KeyError:
            raise HTTPBadRequest(description="Tenure must be an allowed type.")

        ca.active = True

        if "mail_to" in body:
            ca.mail_to = body["mail_to"]

        self.session.commit()
        contact.lives_at = ca.id
        self.session.commit()

    def on_delete(self, req, resp, id):
        """
        Set an address to inactive
        """

        body = req.get_media()
        contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound("Contact not found")

        if not contact.view_guard(req.context.user):
            raise HTTPForbidden

        if "uprn" not in body and "address" not in body:
            raise HTTPBadRequest(
                description="You must include EITHER a custom address string, or an address UPRN."
            )

        ca = self.__get_contact_address(contact, body)
        if ca is None:
            raise HTTPNotFound(description="Address not found")

        ca.active = False

        self.session.commit()

        resp.status = HTTP_204

    def __get_contact_address(self, contact: Contact, body) -> ContactAddress:
        address = None

        if "uprn" in body:
            address: ContactAddress = (
                self.session.query(ContactAddress)
                .filter(ContactAddress.contact_id == contact.id)
                .filter(ContactAddress.uprn == body["uprn"])
                .first()
            )

        elif "address" in body:
            address: ContactAddress = (
                self.session.query(ContactAddress)
                .filter(ContactAddress.contact_id == contact.id)
                .filter(ContactAddress.custom_address == body["address"])
                .first()
            )

        return address
