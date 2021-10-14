import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

URL = "{engine}://{username}:{password}@{host}:{port}/{database}".format(
    **settings.DATABASE
)
engine = create_engine(URL)

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


Model = declarative_base()
