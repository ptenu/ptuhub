class InvalidPermissionError(Exception):
    pass


def has_all(*args):
    try:
        for a in args:
            result = a()
        return result != False

    except InvalidPermissionError:
        return False


def has_one(*args):
    found = False
    for a in args:
        try:
            result = a()
            if result != False:
                found = True
        except InvalidPermissionError:
            continue

    return found


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
