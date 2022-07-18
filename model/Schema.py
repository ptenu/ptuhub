from datetime import datetime, date
import inspect
import json
import types
from model import Model


class InvalidSchema(Exception):
    pass


class FieldNotAllowed(Exception):
    pass


class Schema:
    def __init__(
        self,
        parent: object,
        fields: list = [],
        whitelist: bool = True,
        custom_fields: dict = {},
    ) -> None:
        """
        parent:         this is the Model object which is being schemarised
        fields:         a list of fields to exclude/include in the schema
        whitelist:      if True, the fields property will be used as a whitelist (i.e. only
                        the fields listed will be returned in the schema). If False, the fields
                        property will be used as a blacklist; all fields in the object will be
                        returned except those listed.
        custom_fields:  a dictionary of custom properties to be added into the schema. These
                        will overload any 'real' properties of the parent object.
        """

        self.__object__ = parent
        self.__fields__ = []
        self.__custom__ = None
        self.__map__ = {}

        if custom_fields is not None:
            self.__custom__ = custom_fields

        for key in dir(self.__object__):
            if key in self.__fields__:
                continue

            if (
                key.startswith("__")
                or key.startswith("_")
                or key.endswith("_guard")
                or key.endswith("_filter")
            ):
                continue

            if len(fields) > 0:
                if not whitelist and key in fields:
                    continue

                if whitelist and key not in fields:
                    continue

            self.__fields__.append(key)

        self.setup()

    def setup(self):
        for field_name in self.__fields__:
            if not hasattr(self.__object__, field_name):
                raise InvalidSchema

            field_value = getattr(self.__object__, field_name)
            self.__map__[field_name] = field_value

        self.__map__ = {**self.__map__, **self.__custom__}

    def __validate_obj(self, object, user):
        if isinstance(object, datetime) or isinstance(object, date):
            return object.isoformat()

        is_a_model = issubclass(type(object), Model)
        if is_a_model:
            try:
                allowed = object.view_guard(user)
                if allowed == False:
                    return False
            except:
                return False

        if not hasattr(object, "__schema__"):
            try:
                value = json.dumps(object)
                return object
            except:
                try:
                    value = str(object)
                    return value
                except:
                    return False

        schema = getattr(object, "__schema__")
        if callable(schema):
            return object.__schema__().toDict(user)

        return False

    def toDict(self, user=None, include: list = []):
        """
        Go through all fields specified and return them as a dict
        Also, recursivley expand child objects
        """

        output_dict = {}

        for property in self.__map__:
            if len(include) > 0 and property not in include:
                continue

            property_value = []
            property_object = self.__map__[property]

            filter_method_name = f"{property}_filter"
            if hasattr(self.__object__, filter_method_name):
                filter_method = getattr(self.__object__, filter_method_name)
                if filter_method(user) == False:
                    continue

            if isinstance(property_object, list):
                for member in property_object:
                    v = self.__validate_obj(member, user)
                    if v == False:
                        continue

                    if v in property_value:
                        continue

                    property_value.append(v)

            else:
                property_value = self.__validate_obj(property_object, user)

            if property_value:
                output_dict[property] = property_value

        output_dict = dict(sorted(output_dict.items()))

        return output_dict
