class InvalidPermissionError(Exception):
    pass


def has_all(*args):
    pass


def has_one(*args):
    pass


def e2b(func, *args, **kwargs):
    """
    Error to bool - Calls a function within a try loop which
    catches InvalidPermissionErrors and returns a boolean value
    which represents whether the permission is valid or not.
    """

    try:
        func(*args, **kwargs)
        return True
    except InvalidPermissionError:
        return False


def trusted_user(user):
    try:
        assert user is not None
        assert user.account_blocked != True
    except AssertionError:
        raise InvalidPermissionError


def user_has_role(user, role: str):
    roles = []
    for r in user.roles:
        roles.append(r.name)

    try:
        assert role in roles
    except AssertionError:
        raise InvalidPermissionError
