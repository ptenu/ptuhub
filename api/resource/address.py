from datetime import datetime
import json

from api.middleware.authentication import EnforceRoles
import falcon
from falcon.errors import HTTPNotFound, HTTPUnauthorized, HTTPBadRequest
from model.Address import Address, AddressNote, Postcode, Street, SurveyReturn
from model.Contact import Contact
from api.schemas.address import AddressSchema, StreetSchema


class AddressResource:
    @falcon.before(EnforceRoles, ["organiser", "rep", "officer"])
    def on_get(self, req, resp, uprn):

        addr = self.session.query(Address).get(uprn)

        if addr is None:
            raise HTTPNotFound

        schema = AddressSchema(addr)
        resp.text = json.dumps(schema.extended)

    @falcon.before(EnforceRoles, ["organiser", "rep", "officer"])
    def on_get_notes(self, req, resp, uprn):
        """
        Get all notes for an address
        """

        addr = self.session.query(Address).get(uprn)

        if addr is None:
            raise HTTPNotFound

        schema = AddressSchema(addr)
        resp.text = json.dumps(schema.notes)

    @falcon.before(EnforceRoles, ["organiser", "rep", "officer"])
    def on_put_notes(self, req, resp, uprn):
        """
        Add a note to an address
        """

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

    @falcon.before(EnforceRoles, ["organiser", "rep", "officer"])
    def on_delete_note(self, req, resp, uprn, id):
        """
        Set a note as withdrawn
        """

        note: AddressNote = self.session.query(AddressNote).get(id)
        if note is None:
            raise HTTPNotFound

        note.withdrawn = True
        self.session.commit()
        resp.status = 204

    def on_get_postcode(self, req, resp, outcode: str, incode: str):
        """
        Return a list of all addresses in a postcode unit
        """

        pc_string = f"{outcode} {incode}".upper()
        pc: Postcode = self.session.query(Postcode).get(pc_string)
        if pc is None:
            raise HTTPNotFound

        addresses = (
            self.session.query(Address)
            .filter(Address.postcode == pc.pcds)
            .filter(Address.classification_code.startswith("R"))
            .order_by(
                Address.pao_start_number,
                Address.pao_end_number,
                Address.sao_start_number,
                Address.sao_end_number,
                Address.pao_text,
                Address.sao_text,
            )
            .all()
        )

        resp.text = json.dumps(list(map(AddressSchema.map_simple, addresses)))

    def on_get_street(self, req, resp, outcode: str):
        """
        Return a list of streets for a given postcode sector
        * If a district is entered (i.e. PE2) then a list of sectors is returned.
        """
        if req.context.user is None:
            raise HTTPUnauthorized

        if len(outcode) == 3:
            # Get the sectors in a district
            pcds = (
                self.session.query(Postcode)
                .filter(Postcode.pcds.startswith(outcode.upper()))
                .all()
            )

            sectors = []
            for pc in pcds:
                s = pc.pcds[:5]
                if s not in sectors:
                    sectors.append(s)

            resp.text = json.dumps(sectors)
            return

        if len(outcode) == 4:
            sector = outcode[3]
            outcode = outcode[:3]
            outcode = f"{outcode} {sector}".upper()

            usrns = (
                self.session.query(Address.usrn)
                .filter(Address.postcode.startswith(outcode.upper()))
                .distinct()
                .all()
            )

            usrns = list(map(lambda usrn: usrn[0], usrns))

            streets = (
                self.session.query(Street)
                .filter(Street.usrn.in_(usrns))
                .order_by(Street.description)
                .all()
            )
            result = list(map(StreetSchema.map_simple, streets))
            resp.text = json.dumps(result)
            return

        raise HTTPBadRequest(
            title="URL paramater incorrect",
            description="Please enter a postcode district (e.g. PE2) or a sector (e.g. PE25).",
        )

    @falcon.before(EnforceRoles, ["organiser", "rep", "officer"])
    def on_get_returns(self, req, resp, uprn):
        """
        Return a list of data gathered for a specific address
        """

        addr = self.session.query(Address).get(uprn)

        if addr is None:
            raise HTTPNotFound

        result = AddressSchema(addr).returns
        resp.text = json.dumps(result)

    @falcon.before(EnforceRoles, ["organiser", "rep", "officer"])
    def on_put_returns(self, req, resp, uprn):
        """
        Add a new return
        """

        addr = self.session.query(Address).get(uprn)

        if addr is None:
            raise HTTPNotFound

        input = req.get_media()

        if "date" not in input:
            raise HTTPBadRequest(description="You must include a date field.")

        if "added_by" not in input:
            raise HTTPBadRequest(description="You must include a 'added_by' field.")

        response = SurveyReturn()
        response.address = addr

        try:
            date = datetime(input["date"][0], input["date"][1], input["date"][2])
            response.date = date
        except:
            raise HTTPBadRequest(
                description="The date you provided was in the wrong format."
            )

        contact = self.session.query(Contact).get(input["added_by"])
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

        self.session.add(response)
        self.session.commit()

        resp.status = 201


class StreetResource:
    def on_get(self, req, resp, usrn: int):
        """
        Return a list of addresses for a given street
        """
        if req.context.user is None:
            raise HTTPUnauthorized

        street = self.session.query(Street).get(usrn)
        if street is None:
            raise HTTPNotFound

        addresses = (
            self.session.query(Address)
            .filter(Address.usrn == usrn)
            .order_by(
                Address.pao_start_number,
                Address.pao_end_number,
                Address.sao_start_number,
                Address.sao_end_number,
                Address.pao_text,
                Address.sao_text,
            )
            .all()
        )

        addresses = list(map(AddressSchema.map_simple, addresses))
        result = StreetSchema(street).extended(addresses)

        resp.text = json.dumps(result)
