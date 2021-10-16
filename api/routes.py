import api.resource.root as root
import api.resource.contacts as contacts


class Routes:
    """
    Define all routes for the application
    """

    def __init__(self, app):

        app.add_route("/", root.RootResource())

        # Contacts
        app.add_route("/contacts", contacts.ContactsCollection())
        app.add_route("/contacts/{id}", contacts.ContactCollection())
