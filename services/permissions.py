from datetime import date
from model import db
from enum import Enum


class RoleTypes(Enum):
    CHAIR = "chair"
    SEC = "secretary"
    TRES = "treasurer"
    TRUST = "trustee"
    MEM = "member"
    DEL = "delegate"
    REP = "rep"
    SREP = "senior rep"
    ORG = "organiser"
    LREP = "learning rep"


class InvalidPermissionError(Exception):
    pass


def has_all(*args):
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


def user_has_position(
    contact,
    role,
    branch=None,
    committee=None,
    union=False,
):
    from model.Organisation import Committee, RoleTypes, Role

    if role is None:
        raise ValueError

    if branch is not None and committee is not None:
        raise ValueError

    roles = (
        db.query(Role)
        .filter(Role.contact_id == contact.id)
        .filter(Role.held_since < date.today())
        .filter(Role.ends_on > date.today())
    )

    try:
        roles_list = iter(role)
    except TypeError:
        if not isinstance(role, RoleTypes):
            raise ValueError
        roles.filter(Role.type == role)
    else:
        roles.filter(Role.type.in_(roles_list))

    if union:
        roles.join(Role.committee).filter(Committee.access_level == 2)

    if branch is not None:
        roles.filter(Role.branch_id == branch.id)

    if committee is not None:
        roles.filter(Role.committee_id == committee.id)

    try:
        assert roles.count() > 1
    except AssertionError:
        raise InvalidPermissionError


def trusted_user(contact, *args, **kwargs):
    try:
        assert contact is not None
        assert contact.membership_status == "ACTIVE"

    except AssertionError:
        raise InvalidPermissionError


def user_has_role(contact, role):
    return user_has_position(contact, role)
