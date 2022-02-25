"""
Register all middleware in this array:
"""

import api.middleware.database as database
import api.middleware.session as auth
import api.middleware.cors as cors
import api.middleware.guard as guard
from model import db

MIDDLEWARE = [
    cors.OptionsMiddleware(),
    database.SQLAlchemySessionManager(db),
    auth.SessionManager(),
    guard.GuardMiddleware(),
]
