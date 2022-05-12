from model.Contact import Contact
from falcon.errors import (
    HTTPBadRequest,
    HTTPNotImplemented,
    HTTPForbidden,
)


class GuardMiddleware:
    def validate(self, method: str, single_obj, contact: Contact = None, fields=[]):
        """
        For a given object, call the appropriate method on the object and
        return either the object, or False
        """
        rv = False

        if not hasattr(single_obj, method):
            raise HTTPNotImplemented

        attribute = getattr(single_obj, method)

        if not callable(attribute):
            if attribute == False:
                return rv
        else:
            if attribute(contact) == False:
                return rv

        if hasattr(single_obj, "__schema__"):
            if callable(single_obj.__schema__):
                rv = single_obj.__schema__().toDict(contact, fields)
            else:
                rv = single_obj.__schema__.toDict(contact, fields)

        return rv

    def process_response(self, req, resp, resource, req_succeeded):
        if not req_succeeded:
            return

        if req.method == "OPTIONS":
            return

        # Get required data from context, and validate
        contact = req.context.user

        try:
            action = "view"
            obj = resp.context.media
        except AttributeError:
            return

        # i.e. we need both not just one
        if action is None and obj is not None:
            raise HTTPBadRequest(description="Permissions validation error 1.")

        if action is not None and obj is None:
            raise HTTPBadRequest(description="Permissions validation error 2.")

        # ... but if they're both none then we don't care, bail out
        if action is None and obj is None:
            return

        # Get action method string
        method_string = action.lower() + "_guard"

        fields = []
        if "fields" in resp.context:
            fields = resp.context.fields

        if isinstance(obj, list):
            new_list = filter(
                lambda i: i != False,
                map(lambda o: self.validate(method_string, o, contact, fields), obj),
            )
            new_list = list(new_list)
            resp.media = new_list
            return

        obj = self.validate(method_string, obj, contact=contact, fields=fields)
        if obj is False:
            raise HTTPForbidden
        resp.media = obj
