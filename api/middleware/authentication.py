from falcon.errors import HTTPForbidden, HTTPUnauthorized
from model import Session
from services.auth import get_contact_from_token
from model.Subscription import OnboardingToken


class UserAuthManager:
    def __init__(self, db: Session):
        self.db = db

    def process_request(self, req, resp):
        """
        Read the appropriate headers and return the user (if one exists and token is valid)
        """

        onboarding_id = req.get_header("X-Onboarding-Id")
        if onboarding_id is not None and req.auth is None:
            ob_token = self.db.query(OnboardingToken).get(onboarding_id)
            if ob_token is None:
                raise HTTPUnauthorized(
                    description="There was a problem with the token you provided."
                )

            req.context.user = ob_token.contact
            return

        token = req.auth
        if token is None:
            req.context.user = None
            return

        try:
            user = get_contact_from_token(token)
        except:
            raise HTTPUnauthorized(
                description="There was a problem with the token you provided."
            )

        if user is None:
            req.context.user = None
            return

        req.context.user = user


class EnforceRoles:
    """
    Hook to enforce roles
    """

    matching_roles = False

    def __init__(self, req, resp, resource, params, roles):

        contact = req.context.user
        if contact is None:
            raise HTTPUnauthorized

        for r in contact.roles:
            if r.name == "global.admin" or r.name in roles:
                self.matching_roles = True
                break

        if not self.matching_roles:
            raise HTTPForbidden(
                description="User does not have permission to access this resource."
            )

    def __call__(self, **kwargs):
        pass
