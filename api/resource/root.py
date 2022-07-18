import falcon


class RootResource:
    def on_get(self, req, resp):
        """
        Respond to requests to confirm application is running.
        """

        resp.media = {"status": "okay"}
