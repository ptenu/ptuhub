"""
Register all middleware in this array:
"""

import api.middleware.database as database
from model import Session

MIDDLEWARE = [database.SQLAlchemySessionManager(Session)]
