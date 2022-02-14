from model import db
from model.Contact import Contact


def get_branch_members(branch):
    contacts = []

    for area in branch.areas:
        contacts.extend(
            db.query(Contact)
            .filter(Contact.membership_number != None)
            .filter(Contact.postcode.startswith(area.postcode))
            .all()
        )

    return contacts
