import os
import secrets

from passlib.hash import argon2
import chevron
import boto3
import settings
from model import db
from model.Contact import Contact, EmailAddress, VerifyToken
from model.Email import EmailMessage, EmailRecipient
from model.Organisation import Branch, Committee
from falcon.errors import HTTPNotFound, HTTPBadRequest, HTTPInternalServerError

ses = boto3.client(
    "sesv2",
    aws_access_key_id=settings.config["aws"].get("access_key"),
    aws_secret_access_key=settings.config["aws"].get("secret"),
    region_name="eu-west-1",
)


class EmailService:
    CHARSET = "UTF-8"
    FROM_EMAIL = "do_not_reply@email.peterboroughtenants.app"

    def render(
        self,
        template: str,
        recipient: Contact = None,
        sender: Contact = None,
        context={},
    ):
        """
        Render a moustache template and inject the context variables
        """

        base_path = os.getcwd()
        email_path = os.path.abspath(os.path.join(base_path, "templates/emails"))

        if recipient is not None:
            context["recipient_name"] = recipient.given_name
            context["membership_no"] = recipient.membership_number

        if sender is not None:
            context["sender_name"] = sender.name

        if "message" in context:
            context["message"] = chevron.render(context["message"], context)

        path = f"{email_path}/{template}.html"
        with open(path, "r") as t:
            return chevron.render(
                t,
                context,
                partials_path=os.path.join(email_path, "partials/"),
                partials_ext="html",
            )

    def send(
        self,
        to,
        subject,
        body_plain,
        body_html,
        sender="Peterborough Tenants Union",
        reply_to=None,
    ):
        """
        Send an email
        """

        email_config = {
            "FromEmailAddress": f"{sender} <{self.FROM_EMAIL}>",
            "Destination": {"ToAddresses": (to,)},
            "Content": {
                "Simple": {
                    "Subject": {"Data": subject, "Charset": self.CHARSET},
                    "Body": {
                        "Text": {"Data": body_plain, "Charset": self.CHARSET},
                        "Html": {"Data": body_html, "Charset": self.CHARSET},
                    },
                },
            },
        }

        if reply_to is not None:
            email_config["ReplyToAddresses"] = [reply_to]

        ses.send_email(**email_config)

    def get_recipients(self, message: EmailMessage):
        """
        Get full list of email recipients
        """

        contacts = []

        for r in message.recipients:
            if r.type is EmailRecipient.Types.CONTACT:
                contacts.append(db.get(Contact, r.recipient_id))
                continue

            if r.type is EmailRecipient.Types.BRANCH:
                branch = db.get(Branch, r.recipient_id)
                contacts.extend(branch.contacts)
                continue

            if r.type is EmailRecipient.Types.COMMITTEE:
                committee = db.get(Committee, r.recipient_id)
                contacts.extend(committee.members)

        return contacts

    def send_verification(self, address: str):
        """
        Send a verification code to an email address
        """

        code = secrets.randbits(32)
        code = str(code)[:6]
        message = f"[Peterborough Tenants Union]\nYour email verification code is: \n{str(code)}"

        html_message = self.render("verify_code", context={"code": code})

        token = self.db.query(VerifyToken).get([VerifyToken.Types.EMAIL, address])
        if token is None:
            token = VerifyToken()
            token.id = address.upper()
            token.type = VerifyToken.Types.EMAIL
            self.db.add(token)

        token.hash = argon2.hash(str(code))

        self.db.commit()

        self.send(address, "Email address verification code", message, html_message)

    def validate(self, email: str, code: int):
        """
        Verify an email
        """

        token = self.db.query(VerifyToken).get([VerifyToken.Types.EMAIL, email.upper()])
        if token is None:
            raise HTTPNotFound(description="The token you tried to use has expired.")

        if not argon2.verify(code, token.hash):
            raise HTTPBadRequest(description="Invalid code")

        email = self.db.query(EmailAddress).get(email.upper())
        if email is None:
            raise HTTPNotFound(description="The token you tried to use has expired.")

        email.verified = True
        self.db.delete(token)
        self.db.commit()
