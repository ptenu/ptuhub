import secrets

import argon2
import boto3
import settings
from model import Session as db
from model.Contact import Contact, EmailAddress, VerifyToken
from model.Email import EmailMessage, EmailRecipient
from model.Organisation import Branch, Committee
from falcon.errors import HTTPNotFound, HTTPBadRequest

ses = boto3.client(
    "sesv2",
    aws_access_key_id=settings.config["aws"].get("access_key"),
    aws_secret_access_key=settings.config["aws"].get("secret"),
    region_name="eu-west-1",
)


class EmailService:
    CHARSET = "UTF-8"
    FROM_EMAIL = "do_not_reply@email.peterboroughtenants.app"

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
                contacts.extend(branch.members)
                continue

            if r.type is EmailRecipient.Types.COMMITTEE:
                committee = db.get(Committee, r.recipient_id)
                contacts.extend(committee.members)

        return contacts

    def send_verification(self, address: str):
        """
        Send a verification code to an email address
        """

        code = secrets.randbits(24)
        message = f"[Peterborough Tenants Union]\nYour email verification code is: \n{str(code)}"
        html_message = f"""
        <p><strong>Peterborough Tenants Union</strong></p>
        <p>Your email verification code is:</p>
        <h3>{str(code)}</h3>
        <p>To verify your email address, enter this code into the website when prompted. This
        code will be valid for 15 minutes.</p>
        """

        token = VerifyToken()
        token.id = address.upper()
        token.type = VerifyToken.Types.EMAIL
        token.hash = argon2.hash_password(bytes(code))
        self.db.add(token)
        self.db.commit()

        self.send(address, "Email address verification code", message, html_message)

    def validate(self, email: str, code: int):
        """
        Verify an email
        """

        token = self.db.query(VerifyToken).get(VerifyToken.Types.EMAIL, email)
        if token is None:
            raise HTTPNotFound

        if not argon2.verify_password(token.hash, bytes(code)):
            raise HTTPBadRequest(description="Invalid code")

        email = self.db.query(EmailAddress).get(email)
        if email is None:
            raise HTTPNotFound

        email.verified = True
        self.db.delete(token)
        self.db.commit()
