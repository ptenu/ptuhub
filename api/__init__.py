import falcon

import api.middleware
import api.routes as routes

from services.email_worker import start_email_worker

app = falcon.App(middleware=api.middleware.MIDDLEWARE)

# Init routes
routes.Routes(app)

# Start any workers
start_email_worker()
