import api.resource.root as root
import api.resource.contacts as contacts
import api.resource.login as login


class Routes:
    """
    Define all routes for the application
    """

    def __init__(self, app):

        app.add_route("/", root.RootResource())

        # Auth
        app.add_route("/token", login.TokenResource(), suffix="token")
        app.add_route("/password", login.PasswordResource(), suffix="self")
        app.add_route(
            "/password/{contact_id}", login.PasswordResource(), suffix="contact"
        )

        # Contacts
        app.add_route("/contacts", contacts.ContactsResource(), suffix="collection")
        app.add_route("/contacts/{id}", contacts.ContactsResource(), suffix="single")
