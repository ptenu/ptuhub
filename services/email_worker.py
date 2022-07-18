"""
This file monitors the Email queue the whole time the system is running and will
send any emails in priority order.
"""
from abc import ABC
from model.Email import EmailMessage, EmailDelivery
from datetime import datetime
from model import session_factory
from sqlalchemy.orm import scoped_session
import threading
import queue
from services.email import EmailService
from io import StringIO
from html.parser import HTMLParser


class MLStripper(HTMLParser, ABC):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


es = EmailService()

# The number of threads to use to send rendered emails
SEND_THREAD_COUNT = 2

# The number of threads to use to render emails
RENDER_THREAD_COUNT = 2

ready_to_render = queue.Queue(1000)
ready_to_send = queue.PriorityQueue(500)

delivery_lock = threading.Lock()


class RenderedEmail:
    def __init__(self, email: EmailMessage, html: str, delivery: EmailDelivery):
        self.message = email
        self.html = html
        self.delivery = delivery


def collect_pending_emails():
    global ready_to_render
    collection = threading.Event()
    db = scoped_session(session_factory)

    while True:
        emails = (
            db.query(EmailMessage)
            .filter(EmailMessage._status == EmailMessage.Statuses.SCHEDULED)
            .filter(EmailMessage.send_after < datetime.now())
        )
        emails = emails.all()

        if len(emails) < 1:
            collection.wait(5)
            continue

        for e in emails:
            e.status = EmailMessage.Statuses.RENDERING
            db.commit()
            ready_to_render.put(e)


def render_emails():
    global ready_to_render, ready_to_send, delivery_lock
    db = scoped_session(session_factory)

    while True:
        email: EmailMessage = ready_to_render.get()
        recipients = es.get_recipients(email)
        for r in recipients:
            context = {}
            if email.message is not None:
                context["message"] = email.message
            html = es.render(email.template, r, email.created_by, context=context)

            delivery_lock.acquire()
            delivery = EmailDelivery(email.id, r.id)
            db.add(delivery)
            db.commit()
            delivery_lock.release()

            render = RenderedEmail(email, html, delivery)
            ready_to_send.put((email.priority.value, render))
            ready_to_render.task_done()


def send_emails():
    global ready_to_send, delivery_lock
    db = scoped_session(session_factory)

    while True:
        email: RenderedEmail = ready_to_send.get()[1]

        es.send(
            email.delivery.contact.prefered_email,
            email.message.subject,
            strip_tags(email.html),
            email.html,
            email.message.created_by.name,
        )
        ready_to_send.task_done()

        delivery_lock.acquire()

        msg = db.get(EmailMessage, email.message.id)
        dlv = db.get(
            EmailDelivery, (email.delivery.message_id, email.delivery.contact_id)
        )

        if msg is None or dlv is None:
            continue

        dlv.status = EmailDelivery.Statuses.SENT
        msg._status = EmailMessage.Statuses.SENT
        db.commit()
        delivery_lock.release()


def start_email_worker():
    """
    Main function to call from elsewhere
    """

    print("Initialising email worker...\n")

    threading.Thread(target=collect_pending_emails, daemon=True).start()

    for x in range(1, RENDER_THREAD_COUNT):
        threading.Thread(target=render_emails, daemon=True).start()

    for y in range(1, SEND_THREAD_COUNT):
        threading.Thread(target=send_emails, daemon=True).start()
