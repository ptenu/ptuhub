from os import name
from model import db
from model.Contact import Contact, EmailAddress
from passlib.hash import argon2
from services.stripe import import_customers


def create_contact(given_name: str, family_name: str, email: str):
    contact = Contact()
    contact.given_name = given_name.capitalize()
    contact.family_name = family_name.capitalize()
    db.add(contact)
    db.commit()

    new_email = EmailAddress(contact, email.upper())
    new_email.verified = True
    db.add(new_email)
    db.commit()

    contact.prefered_email = email.upper()
    db.commit()


def set_password(contact_id: int, password: str):
    contact = db.query(Contact).get(contact_id)
    if contact is None:
        return False

    contact.password_hash = argon2.hash(password)
    db.commit()
    return True


def import_from_stripe():
    return import_customers()
