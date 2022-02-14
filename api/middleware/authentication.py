from falcon.errors import HTTPForbidden, HTTPUnauthorized


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
