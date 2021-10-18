"""
Register all middleware in this array:
"""

import api.middleware.database as database
import api.middleware.authentication as auth
from model import Session

MIDDLEWARE = [database.SQLAlchemySessionManager(Session), auth.UserAuthManager(Session)]
