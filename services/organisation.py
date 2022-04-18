from sqlalchemy import func
from model import db


def get_branch_members(branch):
    from model.Address import Address
    from model.Contact import Contact, ContactAddress
    from model.Organisation import Branch, BranchArea

    subquery = (
        db.query(Branch)
        .join(Branch.areas)
        .join(ContactAddress, Contact.lives_at == ContactAddress.id)
        .join(Address, Address.uprn == ContactAddress.uprn)
        .filter(Address.postcode.like(BranchArea.postcode + "%"))
        .order_by(func.length(BranchArea.postcode).desc())
        .limit(1)
        .subquery()
    )
    contacts = db.query(Contact).filter(subquery == branch.id).cte()
    return contacts
