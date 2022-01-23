import json
import tempfile

import api.middleware.authentication as auth
import falcon
from api.interface.contacts import ContactInterface
from falcon import HTTP_201, HTTP_204
from falcon.errors import HTTPBadRequest, HTTPNotFound
from api.schemas.contact import ContactSchema
from model.Contact import Contact


class ContactsResource:
    @falcon.before(auth.EnforceRoles, ["officer", "rep", "organiser"])
    def on_get_collection(self, req, resp):
        """
        Get a list of contacts
        """
        contacts = (
            self.session.query(Contact).order_by(Contact._created_on.desc()).all()
        )

        result = list(map(ContactSchema.map_simple, contacts))
        resp.text = json.dumps(result)

    def on_post_collection(self, req, resp):
        """
        Create a new contact
        """

        # Get paramaters from body
        body = req.get_media()

        new_contact = ContactInterface(self.session).create_new_contact(body)
        schema = ContactSchema(new_contact)

        resp.text = json.dumps(schema.extended)

    @falcon.before(auth.EnforceRoles, ["officer", "rep", "organiser"])
    def on_get_single(self, req, resp, id):
        """
        Return a single contact
        """

        contact = self.session.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        schema = ContactSchema(contact)
        resp.text = json.dumps(schema.extended)

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_patch_single(self, req, resp, id):
        """
        Update specified fields on a contact
        """

        body = req.get_media()
        contacts_interface = ContactInterface(self.session)

        updated_contact = contacts_interface.update_contact(id, body)
        schema = ContactSchema(updated_contact)

        resp.text = json.dumps(schema.extended)

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_delete_single(self, req, resp, id):
        """
        Delete a specified contact
        """
        contacts_interface = ContactInterface(self.session)
        contacts_interface.delete_contact(id)
        resp.status = HTTP_204


class AvatarResource:
    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_put(self, req, resp, id):

        form = req.get_media()
        did_the_user_upload_an_image = False

        for part in form:
            if part.name != "avatar":
                continue

            did_the_user_upload_an_image = True

            with tempfile.TemporaryFile() as tmp_image:
                tmp_image.write(part.stream.read())
                contacts_interface = ContactInterface(self.session)
                contacts_interface.put_avatar(id, tmp_image)
                break

        if not did_the_user_upload_an_image:
            raise HTTPBadRequest(
                "Missing parameter",
                "Please include an image you wish to use as an avatar",
            )

        resp.status = HTTP_201

    @falcon.before(auth.EnforceRoles, ["officer"])
    def on_delete(self, req, resp, id):
        ci = ContactInterface(self.session)
        ci.clear_avatar(id)

        resp.status = HTTP_204
