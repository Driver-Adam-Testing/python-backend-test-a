from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException

from app.auth.api_key_middleware import require_api_key
from app.auth.jwt_middleware import require_jwt, require_m2m_jwt
from app.auth.models import M2M, User
from app.auth.permissions import (
    CONTENT_EDITOR,
    CONTENT_READONLY,
    SUBSCRIPTION_MANAGER,
    USAGE_CREDITOR,
)

if TYPE_CHECKING:
    from collections.abc import Callable

# Paths that do NOT require authentication
# UNPROTECTED_PATHS = {
#     "/login",
#     "/studio/v1/healthcheck/",
#     "/docs",
#     "/studio/v1/openapi.json",
#     "/redoc",
#     "/studio/v1/sandbox/apollo-sandbox/",
#     "/studio/v1/git-provider/github/webhook",
#     "/studio/v1/git-provider/github/callback",
#     "/studio/v1/git-provider/app/callback",
#     "/studio/v1/git-provider/app/webhook",
# }

# Aliases that save typing in route signatures
UserToken = Annotated[User, Depends(require_jwt)]
ApiKeyToken = Annotated[User, Depends(require_api_key)]
M2MToken = Annotated[M2M, Depends(require_m2m_jwt)]


def require_permission(permission: str) -> Callable[[dict[str, Any]], bool]:
    """Factory that returns a dependency enforcing *permission* in JWT."""

    def dep(payload: User = Depends(require_jwt)) -> bool:
        if permission not in payload.permissions:
            raise HTTPException(403, "Insufficient permissions")
        return True

    return dep


# TODO once authorization is fully migrated, there should be no usages of these. Verify!
ContentEditorPermission = Depends(require_permission(CONTENT_EDITOR))
ContentReadonlyPermission = Depends(require_permission(CONTENT_READONLY))
UsageCreditPermission = Depends(require_permission(USAGE_CREDITOR))
SubscriptionManagerPermission = Depends(require_permission(SUBSCRIPTION_MANAGER))
