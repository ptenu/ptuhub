"""
Account API: This resource is for enable users to set up/recover their accounts if
             they have never logged on before.
"""

from falcon import HTTPForbidden, HTTPBadRequest
from model import db
from model.Contact import Contact, EmailAddress
from model.Subscription import Payment


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
            .join(Contact.emails)
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

        challenges = []
        if contact.postcode is not None:
            challenges.append("postcode")

        last_payment = (
            db.query(Payment)
            .filter(Payment.contact_id == contact.id)
            .order_by(Payment.created_on.desc())
            .first()
        )
