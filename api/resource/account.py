"""
Account API: This resource is for enable users to set up/recover their accounts if
             they have never logged on before.
"""

from random import choice
from falcon import HTTPForbidden, HTTPBadRequest, HTTP_204
from model import db
from model.Contact import Contact, EmailAddress, TelephoneNumber
from model.Session import Session
from model.Subscription import Payment
from services.sms import SmsService
from services.email import EmailService


class AccountResource:
    def on_post_identify(self, req, resp):
        """
        Process details provided by a user and return the identity of
        the associated contact, and a challenge.
        """

        if req.context.user is not None:
            raise HTTPForbidden(description="You are already logged in.")

        body = req.get_media()

        try:
            email = str(body["email"]).upper()
            family_name = str(body["family_name"]).upper()

        except:
            raise HTTPBadRequest(description="You must include the required details.")

        contact: Contact = (
            db.query(Contact)
            .join(EmailAddress, Contact.id == EmailAddress.contact_id)
            .filter(EmailAddress.address == email)
            .first()
        )
        if contact is None:
            raise HTTPBadRequest(
                description="The details you entered were not recognised."
            )

        if str(contact.family_name).upper() != family_name:
            raise HTTPBadRequest(
                description="The details you entered were not recognised."
            )

        session: Session = req.context.session
        session.contact_id = contact.id
        db.commit()

        email: EmailAddress = (
            db.query(EmailAddress)
            .filter(
                EmailAddress.contact_id == contact.id, EmailAddress.verified == True
            )
            .first()
        )
        if email is not None:
            ems = EmailService()
            ems.db = db
            ems.send_verification(email.address)
            resp.text = "email"
            return

        phone: TelephoneNumber = (
            db.query(TelephoneNumber)
            .filter(
                TelephoneNumber.contact_id == contact.id,
                TelephoneNumber.verified == True,
            )
            .first()
        )

        if phone is None:
            raise HTTPBadRequest(
                description="You are unable to use this service. Please contact an administrator."
            )
        sms = SmsService(db)
        sms.send_verification(phone.number)
        resp.text = "sms"
        return

    def on_post_recover(self, req, resp):
        """
        Check a verification code and make the session trusted.
        """
        body = req.get_media()

        if req.context.user is None:
            raise HTTPBadRequest()

        contact = req.context.user
        if contact is None:
            raise HTTPBadRequest(description="You must complete identification first.")

        if "sms" in body:
            phone: TelephoneNumber = (
                db.query(TelephoneNumber)
                .filter(
                    TelephoneNumber.contact_id == contact.id,
                    TelephoneNumber.verified == True,
                )
                .first()
            )

            if phone is None:
                raise HTTPBadRequest(
                    description="You are unable to use this service, please contact an administrator."
                )

            sms = SmsService(db)
            sms.validate(phone.number, body["sms"])

        if "email" in body:
            email: EmailAddress = (
                db.query(EmailAddress)
                .filter(
                    EmailAddress.contact_id == contact.id, EmailAddress.verified == True
                )
                .first()
            )
            if email is None:
                raise HTTPBadRequest(
                    description="You are unable to use this service, please contact an administrator."
                )

            ems = EmailService()
            ems.db = db
            ems.validate(email.address, body["email"])

        session: Session = req.context.session
        session.trusted = True
        db.commit()
        resp.status = HTTP_204
