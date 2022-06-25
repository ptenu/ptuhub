from os import name
from model import db
from model.Contact import Contact, EmailAddress
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


def import_from_stripe():
    return import_customers()
