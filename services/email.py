import boto3
import falcon
import settings
from model.Email import EmailMessage, EmailRecipient
from model.Contact import Contact
from model.Organisation import Branch, Committee

from model import Session as db

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
            "Destination": {"ToAddresses": [to]},
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
