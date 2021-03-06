import api.resource.address as address
import api.resource.contacts as contacts
import api.resource.content as content
import api.resource.membership as membership
import api.resource.organisation as org
import api.resource.root as root


class Routes:
    """
    Define all routes for the application
    """

    def __init__(self, app):

        app.add_route("/", root.RootResource())

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
        app.add_route("/contacts/{id}/note", contacts.ContactsResource(), suffix="note")
        app.add_route(
            "/contacts/{id}/note/{note_id}", contacts.ContactsResource(), suffix="note"
        )
        app.add_route(
            "/contacts/{id}/consent", contacts.ContactsResource(), suffix="consent"
        )
        app.add_route(
            "/contacts/{id}/consent/{consent_id}",
            contacts.ContactsResource(),
            suffix="consent",
        )
        app.add_route(
            "/contacts/{id}/phone/{number}", contacts.ContactsResource(), suffix="sms"
        )
        app.add_route("/verify", contacts.ContactsResource(), suffix="verify")
        app.add_route("/contacts/{id}/address", contacts.AddressResource())
        app.add_route(
            "/contacts/{id}/address/{address_id}",
            contacts.AddressResource(),
            suffix="single",
        )

        # Membership
        app.add_route("/membership/{contact_id}", membership.MembershipResource())

        # Address
        app.add_route("/addresses", address.AddressResource())
        app.add_route("/addresses/{uprn}", address.AddressResource(), suffix="single")
        app.add_route(
            "/addresses/{uprn}/notes", address.AddressResource(), suffix="notes"
        )
        app.add_route(
            "/addresses/{uprn}/notes/{id}", address.AddressResource(), suffix="note"
        )
        app.add_route(
            "/addresses/{uprn}/returns", address.AddressResource(), suffix="returns"
        )
        app.add_route("/streets", address.StreetResource())

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

        # Organisation
        app.add_route("/branches", org.BranchResource())
        app.add_route("/branches/{branch_id}", org.BranchResource(), suffix="single")
        app.add_route("/committees", org.CommitteeResource())
        app.add_route(
            "/committees/{committee_id}", org.CommitteeResource(), suffix="single"
        )
        app.add_route("/role", org.RoleResource())
        app.add_route(
            "/contact/{id}/role/{role_id}", org.RoleResource(), suffix="single"
        )
