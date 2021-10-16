from os import name
from model import Session as db
from model.Contact import Contact, EmailAddress


def create_contact(given_name, family_name, email):
    contact = Contact()
    contact.given_name = given_name
    contact.family_name = family_name
    db.add(contact)
    db.commit()

    new_email = EmailAddress()
    new_email.address = str(email).upper()
    new_email.contact = contact
    new_email.verified = True
    db.add(new_email)
    db.commit()

    contact.prefered_email = str(email).upper()
    db.commit()
