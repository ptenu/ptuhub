from model.Contact import Contact
from falcon.errors import HTTPUnauthorized, HTTPBadRequest, HTTPNotImplemented


class GuardMiddleware:
    def validate(self, method: str, single_obj, contact: Contact = None):
        """
        For a given object, call the appropriate method on the object and
        return either the object, or None
        """
        if not hasattr(single_obj, method):
            raise HTTPNotImplemented

        attribute = getattr(single_obj, method)

        if not callable(attribute):
            if attribute:
                return single_obj

        if attribute(contact):
            return single_obj

        return False

    def process_response(self, req, resp, resource, req_succeeded):
        if not req_succeeded:
            return

        # Get required data from context, and validate
        contact = req.context.user

        try:
            action = resp.context.action
            obj = resp.context.media
        except AttributeError:
            return

        # i.e. we need both not just one
        if action is None and obj is not None:
            raise HTTPBadRequest(description="Permissions validation error.")

        if action is not None and obj is None:
            raise HTTPBadRequest(description="Permissions validation error.")

        # ... but if they're both none then we don't care, bail out
        if action is None and obj is None:
            return

        # Get action method string
        method_string = action.lower() + "_guard"

        if isinstance(obj, list):
            obj = filter(lambda o: self.validate(method_string, o, contact), obj)

        try:
            func = resp.context.sfunc
        except:
            return

        if func is None:
            return

        resp.media = func(obj)
