from sqlalchemy import func
from model import db
from datetime import date, timedelta


def get_membership_status(contact):
    from model.Contact import Contact
    from model.Subscription import Membership

    contact: Contact = contact

    if contact.joined_on is None or contact.membership_number is None:
        return "NONE"

    if len(contact.memberships) < 1:
        return "NONE"

    if contact.joined_on > date.today() - timedelta(weeks=4):
        return "PROVISIONAL"

    most_recent_payment: Membership = contact.memberships[0]
    if most_recent_payment is not None and most_recent_payment.status in (
        Membership.Statuses.CANCELLED,
        Membership.Statuses.REJECTED,
        Membership.Statuses.SUSPENDED,
    ):
        return most_recent_payment.status

    if contact.payments_paused:
        return "ACTIVE"

    arrears_period: timedelta = date.today() - contact.joined_on
    if (arrears_period.days / 7) > 15:
        arrears_period = timedelta(weeks=15)

    recent_valid_payments = (
        db.query(Membership)
        .join(Membership.contact)
        .filter(Contact.id == contact.id)
        .filter(Membership.period_start > date.today() - arrears_period)
        .filter(Membership.status == Membership.Statuses.PAID)
        .count()
    )

    if recent_valid_payments == 0:
        return "LAPSED"

    # if recent_valid_payments < 3:
    #     return "ARREARS"

    return "ACTIVE"
