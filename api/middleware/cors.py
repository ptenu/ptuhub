class OptionsMiddleware:
    def process_request(self, req, resp):
        if req.method == "OPTIONS":
            resp.status = 200
            resp.complete = True
