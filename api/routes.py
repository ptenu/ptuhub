import api.resource.root as root
import api.resource.contacts as contacts
import api.resource.login as login
import api.resource.content as content


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
