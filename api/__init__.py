import falcon

import api.middleware
import api.routes as routes

app = falcon.App(middleware=api.middleware.MIDDLEWARE, cors_enable=True)

# Init routes
routes.Routes(app)
