from configparser import Error
from re import L
from string import ascii_uppercase
import random
from sqlalchemy import or_

from stripe.api_resources import customer, subscription
import settings
import stripe
from falcon import HTTPInternalServerError
from model import db
from model.Address import Address
from model.Contact import Contact, ContactAddress, EmailAddress, TelephoneNumber
from operator import itemgetter

STRIPE_KEY = settings.config["stripe"].get("stripe_priv_key")
stripe.api_key = STRIPE_KEY

UK_COUNTRY_CODE = "GB"


def import_customers():
    """
    This will go through all customers in Stripe and create contacts for them
    or update existing contacts
    """

    customers = stripe.Customer.list(limit=100)

    imported = 0
    skipped = 0

    for c in customers.data:

        # Filter out customers we don't want to import
        if c.address is None:
            skipped += 1
            continue

        if c.email is None:
            skipped += 1
            continue

        if "membership_number" not in c.metadata:
            skipped += 1
            continue

        if c.name is None:
            skipped += 1
            continue

        contact: Contact = (
            db.query(Contact)
            .filter(
                or_(
                    Contact.stripe_customer_id == c.id,
                    Contact.prefered_email == str(c.email).upper(),
                )
            )
            .first()
        )

        if contact is None:
            contact = Contact()
            given_name, family_name = str(c.name).split(" ", 1)
            contact.family_name = family_name
            contact.given_name = given_name

            db.add(contact)
            db.commit()

        if contact.prefered_email is None:
            email = EmailAddress(contact, c.email)
            db.add(email)
            db.commit()
            contact.prefered_email = str(email.address).upper()

        if contact.prefered_phone is None and c.phone is not None:
            telephone = TelephoneNumber(c.phone)
            contact.phone_numbers.append(telephone)
            db.commit()
            contact.prefered_phone = telephone.number

        addresses = (
            db.query(Address).filter(Address.postcode == c.address.postal_code).all()
        )
        address = None
        if len(addresses) > 0:
            for a in addresses:
                if a.multiline[0] != c.address.line1:
                    continue
                address = a

        prev_addrs = (
            db.query(ContactAddress)
            .filter(
                ContactAddress.contact_id == contact.id,
                ContactAddress.uprn == address.uprn,
            )
            .all()
        )
        for pa in prev_addrs:
            db.delete(pa)

        new_addr = ContactAddress()
        new_addr.contact = contact

        if "initial_membership_type" in c.metadata:
            if c.metadata.initial_membership_type == "STANDARD":
                new_addr.tenure = ContactAddress.Tenure.RENT_PRIVATE
            else:
                new_addr.tenure = ContactAddress.Tenure.OCCUPIER

        if address is not None:
            new_addr.uprn = address.uprn
        else:
            for line in c.address:
                new_addr.custom_address += c.address[line]

        db.add(new_addr)
        db.commit()
        contact.lives_at = new_addr.id

        contact.stripe_customer_id = c.id
        contact.membership_number = c.metadata.membership_number

        db.commit()
        imported += 1

    return imported, skipped


def get_customer(contact: Contact):
    """
    This will get a customer object for a contact, if it exists, or
    create a new one using the details of the specified contact.
    """
    if contact.stripe_customer_id is not None:
        customer = stripe.Customer.retrieve(contact.stripe_customer_id)
        if customer is not None:
            return customer

    customers = stripe.Customer.list(email=contact.prefered_email)
    if len(customers.data) > 1:
        return customers.data[0]

    address = (
        db.query(ContactAddress)
        .filter(ContactAddress.contact_id == contact.id)
        .filter(ContactAddress.active == True)
        .filter(ContactAddress.tenure is not ContactAddress.Tenure.LANDLORD)
        .first()
    )

    address: Address = address.address

    if address is None:
        raise HTTPInternalServerError(description=f"Invalid address for {contact.name}")

    try:
        customer = stripe.Customer.create(
            name=contact.name(legal=True),
            email=contact.prefered_email,
            phone=contact.prefered_phone,
            address={
                "line1": address.multiline[0],
                "line2": address.multiline[1],
                "city": address.street.town,
                "postal_code": address.postcode,
            },
            metadata={
                "source": "hub-app-v2",
                "postcode": address.postcode,
                "membership_number": contact.membership_number,
            },
        )
    except stripe.error.StripeError as e:
        raise HTTPInternalServerError(description=e.user_message)

    contact.stripe_customer_id = customer.id
    db.commit()

    return customer


def generate_membership_number(contact: Contact):
    year = hex(contact._created_on.year)[2:].upper()
    id_num = str(contact.id).zfill(4)
    month = contact._created_on.month
    membership_number = f"{ascii_uppercase[month]}{year}{id_num}"

    ENV = settings.config["default"].get("env")
    if ENV.startswith(("dev", "DEV")):
        rando = random.randint(10, 99)
        membership_number = f"D{id_num}D{rando}"[:11]
    if ENV.startswith(("test", "TEST", "tst", "TST")):
        rando = random.randint(10, 99)
        membership_number = f"T{id_num}T{rando}"[:11]

    return membership_number


def create_new_membership(contact: Contact):
    """
    Creates a new membership for an existing contact.
    """

    # Delete existing subscriptions so we don't accidently charge them twice
    old_subs = stripe.Subscription.list(customer=customer["id"])
    if len(old_subs) > 0:
        for s in old_subs.data:

            stripe.Subscription.delete(s["id"])
