"""
Register all middleware in this array:
"""
import falcon
from sqlalchemy import true

import api.middleware.database as database
import api.middleware.session as auth
import api.middleware.guard as guard
from model import db

ORIGINS = [
    "https://api.peterboroughtenants.app",
    "http://localhost:3333",
    "http://localhost:8000",
    "http://localhost:1234",
]

MIDDLEWARE = [
    falcon.CORSMiddleware(allow_credentials=ORIGINS, allow_origins=ORIGINS),
    database.SQLAlchemySessionManager(db),
    auth.SessionManager(),
    guard.GuardMiddleware(),
]
