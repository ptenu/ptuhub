import api.resource.root as root
import api.resource.contacts as contacts
import api.resource.login as login
import api.resource.content as content
import api.resource.address as address


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
        app.add_route("/refresh", login.TokenResource(), suffix="refresh")
        app.add_route("/.well-known/jwpub.pem", login.TokenResource(), suffix="pk")

        # Contacts
        app.add_route("/contacts", contacts.ContactsResource(), suffix="collection")
        app.add_route("/contacts/{id}", contacts.ContactsResource(), suffix="single")
        app.add_route("/contacts/{id}/avatar", contacts.AvatarResource())
        app.add_route(
            "/contacts/{id}/email", contacts.ContactsResource(), suffix="email"
        )
        app.add_route("/contacts/{id}/phone", contacts.ContactsResource(), suffix="sms")
        app.add_route(
            "/contacts/{id}/email/{address}",
            contacts.ContactsResource(),
            suffix="email",
        )
        app.add_route(
            "/contacts/{id}/phone/{number}", contacts.ContactsResource(), suffix="sms"
        )
        app.add_route("/verify", contacts.ContactsResource(), suffix="verify")

        # Address
        app.add_route("/address/{uprn}", address.AddressResource())
        app.add_route(
            "/address/{uprn}/notes", address.AddressResource(), suffix="notes"
        )
        app.add_route(
            "/address/{uprn}/notes/{id}", address.AddressResource(), suffix="note"
        )
        app.add_route(
            "/address/{uprn}/returns", address.AddressResource(), suffix="returns"
        )
        app.add_route(
            "/postcode/{outcode}/{incode}", address.AddressResource(), suffix="postcode"
        )
        app.add_route("/postcode/{outcode}", address.AddressResource(), suffix="street")
        app.add_route("/street/{usrn}", address.StreetResource())

        # Content
        app.add_route("/pages", content.PublicPageResource(), suffix="all")
        app.add_route(
            "/pages/category/{category}",
            content.PublicPageResource(),
            suffix="category",
        )
        app.add_route("/pages/{slug}", content.PublicPageResource(), suffix="page")
        app.add_route("/pages/manage", content.AdminPageResource(), suffix="pages")
        app.add_route(
            "/pages/manage/{slug}", content.AdminPageResource(), suffix="page"
        )
