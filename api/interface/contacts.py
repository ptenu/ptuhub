from datetime import datetime
import tempfile
from falcon.errors import HTTPBadRequest, HTTPNotFound
from model import db as Session
from model.File import File
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from model.Contact import Contact
from services.files import FileService


class ContactInterface:
    def __init__(self, session: Session):
        self.db = session

    def create_new_contact(self, input):
        """
        Create a new contact
        """

        new_contact = Contact()
        self.db.add(new_contact)

        try:
            if "given_name" in input:
                new_contact.given_name = input["given_name"]

            if "family_name" in input:
                new_contact.family_name = input["family_name"]

            if "other_names" in input:
                new_contact.other_names = input["other_names"]

            if "first_language" in input:
                new_contact.first_language = input["first_language"]

            if "pronouns" in input:
                new_contact.pronouns = input["pronouns"]

            if "date_of_birth" in input:
                new_contact.date_of_birth = datetime(
                    input["date_of_birth"][0],
                    input["date_of_birth"][1],
                    input["date_of_birth"][2],
                )
        except:
            raise HTTPBadRequest

        self.db.commit()

        return new_contact

    def update_contact(self, id, input):
        """
        Perform a partial update on a contact
        """

        contact: Contact = self.db.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        try:
            if "given_name" in input:
                contact.given_name = input["given_name"]

            if "family_name" in input:
                contact.family_name = input["family_name"]

            if "other_names" in input:
                contact.other_names = input["other_names"]

            if "first_language" in input:
                contact.first_language = input["first_language"]

            if "pronouns" in input:
                contact.pronouns = input["pronouns"]

            if "date_of_birth" in input:
                contact.date_of_birth = datetime(
                    input["date_of_birth"][0],
                    input["date_of_birth"][1],
                    input["date_of_birth"][2],
                )
        except:
            raise HTTPBadRequest

        self.db.commit()

        return contact

    def delete_contact(self, id):
        """
        Delete a contact
        """

        contact = self.db.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        self.db.delete(contact)
        self.db.commit()

        return

    def put_avatar(self, id, input_img):
        """
        Upload an avatar and attach it to the user
        """

        contact: Contact = self.db.query(Contact).get(id)
        if contact is None:
            raise HTTPNotFound

        output_img = tempfile.TemporaryFile()
        input_img.seek(0)

        try:
            with Image.open(input_img) as image:
                image = image.resize((320, 320))
                image = image.convert("RGB")
                image.save(output_img, "jpeg")

        except TypeError:
            raise HTTPBadRequest(
                title="File type not allowed",
                description="Unsupported image file, please try using a JPEG or PNG file (others are supported).",
            )

        except UnidentifiedImageError:
            raise HTTPBadRequest(
                title="File type not allowed",
                description="Please upload an image file.",
            )

        # Create File object
        fs = FileService()
        file = File()
        file.name = f"** Avatar for {contact.name} **"
        file.mime_type = "image/jpeg"
        file.ext = "jpeg"
        file.size = output_img.tell()
        file.delete_after = None

        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        new_file_key = f"usrimg/{contact.id}/{timestamp}.{file.ext}"

        output_img.seek(0)
        file.bucket, file.key = fs.store_file_public(output_img, new_file_key)
        output_img.close()
        file.public_url = fs.get_public_url(file)

        if contact.avatar_id is not None:
            fs.erase_file(contact.avatar.bucket, contact.avatar.key)
            self.db.delete(contact.avatar)

        self.db.add(file)
        self.db.commit()

        contact.avatar_id = file.id

        self.db.commit()

        return file

    def clear_avatar(self, contact_id):
        contact: Contact = self.db.query(Contact).get(contact_id)
        if contact is None:
            raise HTTPNotFound

        fs = FileService()
        if contact.avatar_id is not None:
            fs.erase_file(contact.avatar.bucket, contact.avatar.key)
            self.db.delete(contact.avatar)

        self.db.commit()
