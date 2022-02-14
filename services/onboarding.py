from configparser import Error
from string import ascii_uppercase
import random

from stripe.api_resources import customer, subscription
from model.Subscription import Activity, Subscription
import settings
import stripe
from falcon import HTTPInternalServerError
from model import db
from model.Address import Address
from model.Contact import Contact, ContactAddress
from operator import itemgetter

STRIPE_KEY = settings.config["stripe"].get("stripe_priv_key")
stripe.api_key = STRIPE_KEY


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
            address={
                "line1": address.multiline[0],
                "line2": address.multiline[1],
                "city": address.street.town,
                "postal_code": address.postcode,
            },
            metadata={"source": "hub-app-v2", "postcode": address.postcode},
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


def get_stripe_discount(discount_codes):
    if len(discount_codes) < 1:
        return None, 0

    discounts = stripe.Coupon.list()

    valid_discounts = []
    for d in discounts.data:
        if "hub_code" not in d.metadata:
            continue

        if d.metadata.code in discount_codes:
            valid_discounts.append(d)

    if len(valid_discounts) < 1:
        return None, 0

    cheapest_discount = None
    for d in valid_discounts:
        if cheapest_discount is None:
            cheapest_discount = d
            continue

        if d["percent_off"] > cheapest_discount["percent_off"]:
            cheapest_discount = d
            continue

    return cheapest_discount["id"], cheapest_discount["percent_off"]


def get_best_price(contact: Contact):
    sub = contact.active_subscription
    if sub is None:
        return Error("Subscription not available.")

    products = stripe.Product.list(active=True)

    valid_products = []
    for p in products.data:
        if "membership_type" not in p.metadata:
            continue
        if p.metadata.membership_type == sub.type.name:
            valid_products.append(p)

    if len(valid_products) < 1:
        raise HTTPInternalServerError(description="No products available")

    prices = stripe.Price.list(
        active=True, type="recurring", product=valid_products[0]["id"]
    )

    prices = prices.data
    if len(prices) < 1:
        raise HTTPInternalServerError(description="No prices available")

    prices = sorted(prices, key=itemgetter("created"), reverse=True)

    return prices[0]["id"], prices[0]["unit_amount"]


def create_new_membership(contact: Contact):
    """
    Creates a new membership for an existing contact.
    """

    if contact.membership_number is None:
        contact.membership_number = generate_membership_number(contact)

    sub = contact.active_subscription
    if sub is None:
        sub = Subscription(contact)
        db.add(sub)

    address = (
        db.query(ContactAddress)
        .filter(ContactAddress.contact_id == contact.id)
        .filter(ContactAddress.active == True)
        .filter(ContactAddress.tenure is not ContactAddress.Tenure.LANDLORD)
        .first()
    )

    if address.tenure is ContactAddress.Tenure.OWNER_OCCUPIER:
        sub.type = Subscription.Types.ASSOCIATE

    join_activity = Activity(contact, Activity.Codes.JOINED, subscription=sub)
    db.add(join_activity)

    sub.stripe_price_id, sub.base_rate = get_best_price(contact)

    if sub.id is None:
        subscription = stripe.Subscription.create(
            customer=contact.stripe_customer_id,
            items=[{"price": sub.stripe_price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )
        sub.id = subscription["id"]

    db.commit()

    customer = get_customer(contact)

    # Delete existing subscriptions so we don't accidently charge them twice
    old_subs = stripe.Subscription.list(customer=customer["id"])
    if len(old_subs) > 0:
        for s in old_subs.data:
            if s["id"] == sub.id:
                continue

            stripe.Subscription.delete(s["id"])

    codes = []
    for attr in contact.attributes:
        if (
            str(attr.key).upper() in ("NOT_WORKING", "FTE", "LOW_INCOME")
            and attr.val == "Y"
        ):
            codes.append(str(attr.key).upper())

    sub.stripe_coupon_id, sub.discount = get_stripe_discount(codes)
    db.commit()
