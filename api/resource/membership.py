import calendar
from datetime import datetime
from model.Subscription import Membership
from services.permissions import e2b, trusted_user, user_has_role

from falcon import HTTPForbidden, HTTPNotFound
from model.Contact import Contact
from sqlalchemy.orm import Session

from services.stripe import get_payment_method


class MembershipResource:
    def on_get(self, req, resp, contact_id):
        """
        Get a contact's membership
        """

        if not e2b(trusted_user, req.context.user, req.context.session):
            raise HTTPForbidden

        db: Session = self.session

        contact: Contact = db.get(Contact, contact_id)
        if contact is None:
            raise HTTPNotFound

        if not e2b(user_has_role, req.context.user, "global.admin"):
            if contact_id != req.context.user.id:
                raise HTTPForbidden

        join_date = None
        if len(contact.memberships) > 0:
            first_month: Membership = contact.memberships[-1]
            join_date = first_month.period_start.isoformat()

        string_rate = "£{:.2f}".format(contact.membership_rate / 100)

        membership_classes = {
            None: None,
            "S": "standard",
            "1": "standard",
            "0": "supporter",
        }

        payment_method = None
        if contact.stripe_payment_method_id is not None:
            method = get_payment_method(contact.stripe_payment_method_id)
            details = method[method.type]
            payment_method = {"type": method.type}

            if method.type == "card":
                days_in_month = calendar.monthrange(
                    details.exp_year, details.exp_month
                )[1]
                payment_method["brand"] = details.brand
                payment_method["number"] = f"**** **** **** {details.last4}"
                payment_method["expires"] = datetime(
                    details.exp_year, details.exp_month, days_in_month
                ).isoformat()

            if method.type == "bacs_debit":
                payment_method["number"] = f"****{details.last4}"
                payment_method["sort_code"] = details.sort_code

        latest_month: Membership = contact.memberships[0]

        payments = []
        for p in contact.payments:
            if len(payments) > 5:
                break

            payments.append(
                {
                    "date": p.created_on.isoformat(),
                    "type": p.type.value,
                    "status": p.status,
                    "amount": p.amount / 100,
                }
            )

        membership = {
            "membership_number": contact.membership_number,
            "class": membership_classes[contact.membership_type],
            "joined_on": join_date,
            "rate": string_rate,
            "payment_method": payment_method,
            "status": latest_month.status.value,
            "renewal_date": latest_month.period_end.isoformat(),
            "payments": payments,
        }

        resp.media = membership
