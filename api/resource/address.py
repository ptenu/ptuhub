from datetime import datetime
import json

from api.middleware.authentication import EnforceRoles
import falcon
from sqlalchemy.sql.expression import func
from falcon.errors import HTTPNotFound, HTTPUnauthorized, HTTPBadRequest, HTTPForbidden
from model.Address import Address, AddressNote, Postcode, Street, SurveyReturn
from model.Contact import Contact
from services.permissions import trusted_user


def distance(latlong1, latlong2):
    return func.sqrt(
        func.pow(latlong1[0] - latlong2[0], 2) + func.pow(latlong1[1] - latlong2[1], 2)
    )


class AddressResource:
    def on_get(self, req, resp):

        params = req.params

        if len(params) < 1:
            raise HTTPBadRequest(
                description="There are a lot of addresses, you must provide a search query."
            )

        addr = self.session.query(Address)

        try:
            trusted_user(req.context.user)
            tu = True
        except:
            tu = False

        if "all" not in params or not tu:
            addr = addr.filter(Address.classification_code.startswith("R"))

        for p in params:
            if p == "postcode":
                pc = str(params[p]).upper()

                postcode = self.session.query(Postcode).get(pc)
                if postcode is None:
                    raise HTTPNotFound(description="That postcode does not exist")
                addr = addr.filter(Address.postcode == pc)

            if p == "street":
                try:
                    usrn = int(params[p])
                except ValueError:
                    raise HTTPBadRequest(description="Street ID must be a number")

                street = self.session.query(Street).get(usrn)
                if street is None:
                    raise HTTPNotFound(description="Street not found.")

                addr = addr.filter(Address.usrn == usrn)

            if p == "near":
                lat, long = str(params[p]).split(",", 1)
                lat, long = float(lat), float(long)
                position = (lat, long)
                bounds = ((lat - 0.0003, lat + 0.0003), (long - 0.0003, long + 0.0003))

                addr = (
                    addr.filter(Address.latitude.between(bounds[0][0], bounds[0][1]))
                    .filter(Address.longitude.between(bounds[1][0], bounds[1][1]))
                    .order_by(distance(position, (Address.latitude, Address.longitude)))
                )

        addr = (
            addr.order_by(
                Address.pao_start_number,
                Address.pao_end_number,
                Address.sao_start_number,
                Address.sao_end_number,
                Address.pao_text,
                Address.sao_text,
            )
            .limit(100)
            .all()
        )
        resp.context.media = addr
        resp.context.fields = [
            "uprn",
            "single_line",
            "street_id",
            "classification",
            "last_visit",
        ]

    def on_get_single(self, req, resp, uprn):
        addr = self.session.query(Address).get(uprn)

        if addr is None:
            raise HTTPNotFound

        resp.context.media = addr
        resp.context.action = "view"

    def on_put_notes(self, req, resp, uprn):
        """
        Add a note to an address
        """

        try:
            trusted_user(req.context.user)
        except:
            raise HTTPForbidden

        addr = self.session.query(Address).get(uprn)

        if addr is None:
            raise HTTPNotFound

        input = req.get_media()

        note = AddressNote()

        for key in input:
            if not hasattr(note, key):
                continue

            setattr(note, key, input[key])

        note.address = addr
        note.added_by = req.context.user
        note.date = datetime.now()

        self.session.add(note)
        self.session.commit()
        resp.status = 201

    def on_delete_note(self, req, resp, uprn, id):
        """
        Set a note as withdrawn
        """

        note: AddressNote = self.session.query(AddressNote).get(id)
        if note is None:
            raise HTTPNotFound

        try:
            trusted_user(req.context.user)
            assert req.context.user.id == note.contact_id
        except:
            raise HTTPForbidden

        note.withdrawn = True
        self.session.commit()
        resp.status = 204

    def on_put_returns(self, req, resp, uprn):
        """
        Add a new return
        """

        try:
            trusted_user(req.context.user)
        except:
            raise HTTPForbidden

        addr = self.session.query(Address).get(uprn)

        if addr is None:
            raise HTTPNotFound

        input = req.get_media()

        if "date" not in input:
            raise HTTPBadRequest(description="You must include a date field.")

        try:
            added_by = input["added_by"]
        except:
            added_by = req.context.user.id

        response = SurveyReturn()
        response.address = addr

        try:
            date = datetime(input["date"][0], input["date"][1], input["date"][2])
            response.date = date
        except:
            raise HTTPBadRequest(
                description="The date you provided was in the wrong format."
            )

        contact = self.session.query(Contact).get(added_by)
        if contact is None:
            raise HTTPBadRequest(description="Specified user not found.")
        response.added_by = contact

        if "tenure" in input:
            tenures = {
                "P": SurveyReturn.TenureTypes.PRIVATE_RENT,
                "S": SurveyReturn.TenureTypes.SOCIAL_RENT,
                "L": SurveyReturn.TenureTypes.LICENSEE,
                "O": SurveyReturn.TenureTypes.OWNER_OCCUPIER,
                "H": SurveyReturn.TenureTypes.HMO,
                "U": SurveyReturn.TenureTypes.OTHER,
            }

            if input["tenure"] not in tenures:
                raise HTTPBadRequest(description="Invalid tenure type")

            response.tenure = tenures[input["tenure"]]

        if "answered" in input:
            if input["answered"] == False:
                response.answered = False

        if "previously_rented" in input:
            response.response_2 = str(input["previously_rented"])[0]

        if "hmo" in input:
            response.response_3 = str(input["hmo"])[0]

        self.session.add(response)
        self.session.commit()

        resp.status = 201


class StreetResource:
    def on_get(self, req, resp):
        """
        Return a list of streets for a given postcode sector
        * If a district is entered (i.e. PE2) then a list of sectors is returned.
        """
        try:
            trusted_user(req.context.user)
        except:
            raise HTTPForbidden

        if "q" not in req.params:
            raise HTTPBadRequest(description="Search parameter missing from URL query.")

        if len(req.params["q"]) < 4:
            raise HTTPBadRequest(
                description="Search string must be at least 4 characters."
            )

        query = req.params["q"].upper()

        streets = (
            self.session.query(Street)
            .filter(Street.description.like(f"%{query}%"))
            .filter(Street.households > 0)
            .order_by(Street.description)
            .limit(15)
            .all()
        )

        resp.context.media = streets
        resp.context.action = "view"
