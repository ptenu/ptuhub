from model.Organisation import Branch, Committee


class BranchResource:
    def on_get(self, req, resp):
        """
        Get a list of all branches
        """

        branches = self.session.query(Branch).all()

        resp.context.media = branches
        resp.context.fields = ["id", "abbreviation", "name", "postcodes", "formal_name"]


class CommitteeResource:
    def on_get(self, req, resp):
        """
        Get a list of all committees
        """

        committees = self.session.query(Committee).all()

        resp.context.media = committees
        resp.context.fields = ["id", "abbreviation", "name"]
