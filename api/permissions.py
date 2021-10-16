# ( Object Class Name, [HTTP Methods], [required roles])
# Global admin will skip permissions

# Special roles:
ADMIN = "global_admin"
PUBLIC = "*"
AUTHENTICATED = "trusted"
MEMBER = "member"

# Methods
GET = "get"
POST = "post"
PUT = "put"
PATCH = "patch"
DELETE = "delete"

PERMISSIONS = [
    # Contacts
    ("Contact", [GET, PATCH, DELETE, PUT], [AUTHENTICATED]),
    ("Contact", [POST], [PUBLIC]),
]
