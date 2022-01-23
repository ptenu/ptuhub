import secrets

import argon2
import boto3
import settings
from falcon.errors import HTTPNotFound, HTTPBadRequest
from model.Contact import Contact, TelephoneNumber, VerifyToken
from sqlalchemy.orm import Session

sns = boto3.client(
    "sns",
    aws_access_key_id=settings.config["aws"].get("access_key"),
    aws_secret_access_key=settings.config["aws"].get("secret"),
    region_name="eu-west-1",
)


class SmsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def send(self, to: Contact, message: str):
        """
        Send a message to a contact via SMS
        """

        phone_number = to.telephone

        endpoints = (
            self.db.query(TelephoneNumber)
            .filter(TelephoneNumber.contact_id == to.id)
            .filter(TelephoneNumber.blocked != True)
            .all()
        )

        if len(endpoints) == 0:
            raise Exception("No valid numbers found for contact.")

        if phone_number not in list(map(lambda n: n.number, endpoints)):
            phone_number = endpoints[0]

        phone_number = f"+44{phone_number[1:]}"

        response = sns.publish(PhoneNumber=phone_number, Message=message)

        return response

    def send_verification(self, number: str):
        """
        Send a verification text to a single number
        """
        code = secrets.randbits(16)
        message = f"[Peterborough Tenants Union]\nYour phone number verification code is: \n{str(code)}"

        token = VerifyToken()
        token.id = number
        token.type = VerifyToken.Types.PHONE
        token.hash = argon2.hash_password(bytes(code))
        self.db.add(token)
        self.db.commit()

        if not number.startswith("+44"):
            number = f"+44{number[1:]}"

        return sns.publish(PhoneNumber=number, Message=message)

    def validate(self, number: str, code: int):
        """
        Verify a number
        """

        token = self.db.query(VerifyToken).get(VerifyToken.Types.PHONE, number)
        if token is None:
            raise HTTPNotFound

        if not argon2.verify_password(token.hash, bytes(code)):
            raise HTTPBadRequest(description="Invalid code")

        tel = self.db.query(TelephoneNumber).get(number)
        if tel is None:
            raise HTTPNotFound

        tel.verified = True
        self.db.delete(token)
        self.db.commit()
