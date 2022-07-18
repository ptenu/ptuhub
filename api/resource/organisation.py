from datetime import date, datetime
from dateutil import relativedelta
from model.Organisation import Branch, BranchArea, Committee, Role, RoleTypes
from services.permissions import InvalidPermissionError, user_has_role
from falcon.errors import HTTPForbidden, HTTPBadRequest, HTTPNotFound
from falcon import HTTP_201, HTTP_204


class BranchResource:
    def on_get(self, req, resp):
        """
        Get a list of all branches
        """

        branches = self.session.query(Branch).all()

        resp.context.media = branches
        resp.context.fields = ["id", "formal_name", "members"]

    def on_get_single(self, req, resp, branch_id):
        """
        Get a branch
        """

        branch: Branch = self.session.query(Branch).get(branch_id)
        if branch is None:
            raise HTTPNotFound

        resp.context.media = branch

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

    def on_patch_single(self, req, resp, branch_id):
        """
        Change a branch
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        body = req.get_media()
        branch: Branch = self.session.query(Branch).get(branch_id)
        if branch is None:
            raise HTTPNotFound

        if "name" in body:
            if body["name"] != branch.name:
                branch.name = str(body["name"]).strip()

        if "abbreviation" in body:
            if body["abbreviation"] != branch.abbreviation:
                branch.abbreviation = str(body["abbreviation"]).upper()[:2]

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

            for a in branch.areas:
                self.session.delete(a)

            for pc in postcodes:
                area = BranchArea()
                area.branch = branch
                area.postcode = str(pc).upper().strip()
                self.session.add(area)

            self.session.commit()

        resp.context.media = branch

    def on_delete_single(self, req, resp, branch_id):
        """
        Delete a Branch
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        branch: Branch = self.session.query(Branch).get(branch_id)
        if branch is None:
            raise HTTPNotFound

        for o in branch.officers:
            self.session.delete(o)

        for a in branch.areas:
            self.session.delete(a)

        self.session.delete(branch)

        resp.status = HTTP_204


class CommitteeResource:
    def on_get(self, req, resp):
        """
        Get a list of all committees
        """

        committees = self.session.query(Committee).all()

        resp.context.media = committees
        resp.context.fields = ["id", "abbreviation", "name"]

    def on_post(self, req, resp):
        """
        Create a new committee
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        committee = Committee()

        try:
            body = req.get_media()

            committee.name = str(body["name"]).strip().capitalize()
            committee.abbreviation = str(body["abbreviation"]).strip().upper()[:2]
            self.session.add(committee)
            self.session.commit()

        except:
            raise HTTPBadRequest

        resp.context.media = committee
        resp.status = HTTP_201

    def on_get_single(self, req, resp, committee_id):
        """
        Get a single committee
        """

        committee = self.session.query(Committee).get(committee_id)
        if committee is None:
            raise HTTPNotFound
        resp.context.media = committee

    def on_patch_single(self, req, resp, committee_id):
        """
        Update a committee
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        committee: Committee = self.session.query(Committee).get(committee_id)
        if committee is None:
            raise HTTPNotFound

        try:
            body = req.get_media()

            if "name" in body:
                committee.name = str(body["name"]).strip().capitalize()

            if "abbreviation" in body:
                committee.abbreviation = str(body["abbreviation"]).strip().upper()

            self.session.commit()

        except:
            raise HTTPBadRequest

        resp.context.media = committee

    def on_delete_single(self, req, resp, committee_id):
        """
        Delete a committee
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        committee: Committee = self.session.query(Committee).get(committee_id)
        if committee is None:
            raise HTTPNotFound

        for r in committee.members:
            self.session.delete(r)

        self.session.delete(committee)
        resp.status = HTTP_204


class RoleResource:
    def on_put(self, req, resp):
        """
        Create a new role holder
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        try:
            body = req.get_media()
            role = Role()

            role.contact_id = body["contact_id"]

            if "branch_id" in body:
                role.branch_id = int(body["branch_id"])
                role.unit_type = Role.UnitTypes.BRANCH

            if "committee_id" in body:
                role.committee_id = int(body["committee_id"])
                role.unit_type = Role.UnitTypes.COMMITTEE

            role.held_since = datetime.now()
            if "term" in body:
                role.ends_on = datetime.now() + relativedelta(months=int(body["term"]))

            role.title = str(body["title"]).capitalize().strip()
            type_code = str(body["type"]).strip().upper()
            role.type = RoleTypes[type_code]

            no_of_members = (
                self.session.query(Role)
                .filter(Role.contact_id == role.contact_id)
                .count()
            )

            role.id = no_of_members + 1

            self.session.add(role)
            self.session.commit()
        except:
            raise HTTPBadRequest

        resp.context.media = role
        resp.status = HTTP_201

    def on_delete_single(self, req, resp, id, role_id):
        """
        Remove a role from someone
        """

        try:
            user_has_role(req.context.user, "global.admin")
        except InvalidPermissionError:
            raise HTTPForbidden

        role: Role = self.session.query(Role).get([role_id, id])
        if role is None:
            raise HTTPNotFound

        self.session.delete(role)

        resp.status = HTTP_204
