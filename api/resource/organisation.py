from model.Organisation import Branch, BranchArea, Committee
from services.permissions import InvalidPermissionError, user_has_role
from falcon.errors import HTTPForbidden, HTTPBadRequest
from falcon import HTTP_201


class BranchResource:
    def on_get(self, req, resp):
        """
        Get a list of all branches
        """

        branches = self.session.query(Branch).all()

        resp.context.media = branches
        resp.context.fields = ["id", "abbreviation", "name", "postcodes", "formal_name"]

    def on_post(self, req, resp):
        """
        Create a new branch
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        body = req.get_media()
        try:
            new_branch = Branch()
            self.session.add(new_branch)

            new_branch.name = str(body["name"]).strip()
            new_branch.abbreviation = str(body["abbreviation"]).upper()[:2]
        except KeyError:
            raise HTTPBadRequest(
                description="You must include a name and an abreviation."
            )

        try:
            self.session.commit()
        except:
            raise HTTPBadRequest(
                description="There was a problem adding this branch to the database - try a different abreviation."
            )

        if "postcodes" in body:
            postcodes = body["postcodes"]
            if not isinstance(postcodes, list):
                raise HTTPBadRequest(description="Postcodes must be a list")

            for pc in postcodes:
                area = BranchArea()
                area.branch = new_branch
                area.postcode = str(pc).upper().strip()
                self.session.add(area)

            self.session.commit()

        resp.context.media = new_branch
        resp.status = HTTP_201


class CommitteeResource:
    def on_get(self, req, resp):
        """
        Get a list of all committees
        """

        committees = self.session.query(Committee).all()

        resp.context.media = committees
        resp.context.fields = ["id", "abbreviation", "name"]
