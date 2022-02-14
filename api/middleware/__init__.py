"""
Register all middleware in this array:
"""

import api.middleware.database as database
import api.middleware.session as auth
from model import db

MIDDLEWARE = [database.SQLAlchemySessionManager(db), auth.SessionManager()]
