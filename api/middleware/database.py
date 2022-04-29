from sqlalchemy.orm import Session


class SQLAlchemySessionManager:
    def __init__(self, session: Session):
        self.Session: Session = session

    def process_resource(self, req, resp, resource, params):
        resource.session = self.Session

    def process_response(self, req, resp, resource, req_succeeded):
        if hasattr(resource, "session"):
            self.Session.remove()
