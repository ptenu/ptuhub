import api.resource.root as root


class Routes:
    """
    Define all routes for the application
    """

    def __init__(self, app):

        app.add_route("/", root.RootResource())
