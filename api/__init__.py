import falcon

import api.middleware
import api.routes as routes

app = falcon.App(middleware=api.middleware.MIDDLEWARE)

# Init routes
routes.Routes(app)
