import secrets

from passlib.hash import argon2
from twilio.rest import Client
from services.zadarma import ZadarmaAPI
import settings
from falcon.errors import HTTPNotFound, HTTPBadRequest
from model.Contact import Contact, TelephoneNumber, VerifyToken
from sqlalchemy.orm import Session

Z_KEY = settings.config["zadarma"].get("key")
Z_SECRET = settings.config["zadarma"].get("secret")
z = ZadarmaAPI(key=Z_KEY, secret=Z_SECRET)


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

        if phone_number[:1] == "0":
            phone_number = "44" + phone_number[1:]

        response = z.call(
            "/v1/sms/send/",
            {"number": phone_number, "message": message, "caller_id": "448007074202"},
            "post",
        )

        return response

    def send_verification(self, number: str):
        """
        Send a verification text to a single number
        """
        code = secrets.randbits(32)
        code = str(code)[:6]
        message = f"Your phone number verification code is: \n{str(code)}"

        token = self.db.query(VerifyToken).get([VerifyToken.Types.PHONE, number])
        if token is None:
            token = VerifyToken()
            self.db.add(token)

        token.id = number
        token.type = VerifyToken.Types.PHONE
        token.hash = argon2.hash(str(code))

        self.db.commit()

        if number[:1] == "0":
            number = "44" + number[1:]

        response = z.call(
            "/v1/sms/send/",
            {"number": number, "message": message, "caller_id": "447488811769"},
            "post",
        )

        return response

    def validate(self, number: str, code):
        """
        Verify a number
        """

        token = self.db.query(VerifyToken).get([VerifyToken.Types.PHONE, number])
        if token is None:
            raise HTTPNotFound

        if not argon2.verify(code, token.hash):
            raise HTTPBadRequest(description="Invalid code")

        tel = self.db.query(TelephoneNumber).get(number)
        if tel is None:
            raise HTTPNotFound

        tel.verified = True
        self.db.delete(token)
        self.db.commit()
