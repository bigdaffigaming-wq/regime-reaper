from enum import Enum
from fastapi import HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional


class Role(str, Enum):
    OWNER = "owner"
    PARTNER = "partner"
    VIEWER = "viewer"


ROLE_HIERARCHY = {
    Role.OWNER: 3,
    Role.PARTNER: 2,
    Role.VIEWER: 1,
}


def require_role(minimum_role: Role):
    def checker(x_user_role: Optional[str] = Header(default="viewer")):
        try:
            role = Role(x_user_role)
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid role")

        if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY[minimum_role]:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {minimum_role} role or higher",
            )
        return role

    return checker


def require_owner():
    return require_role(Role.OWNER)


def require_partner():
    return require_role(Role.PARTNER)


def require_viewer():
    return require_role(Role.VIEWER)
