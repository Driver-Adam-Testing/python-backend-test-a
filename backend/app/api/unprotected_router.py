"""unprotected_router.py

Endpoints that **do not** require a JWT.

These routes are mounted under the same prefix as the main *studio* APIs
(e.g. `/studio/v1`) but are excluded from auth so that uptime checks,
web-hooks, and local sandbox tooling continue to work when the UI is
unauthenticated.
"""

from fastapi import APIRouter

from app.api.routes.legacy.schema import sandbox_router  # GraphQL-Apollo sandbox

# Internal routers -----------------------------------------------------
from app.api.routes.v1 import (
    git_provider,
    healthcheck,
    onboarding,
    signup,
    subscription,
)  # webhook / callback paths
from app.core.config import settings

unprotected_router = APIRouter()

# /studio/v1/healthcheck/** -------------------------------------------
unprotected_router.include_router(
    healthcheck.router, prefix="/healthcheck", tags=["healthcheck"]
)

# /studio/v1/git-provider/github/** (webhooks & OAuth callbacks) ------
unprotected_router.include_router(
    git_provider.router, prefix="/git-provider", tags=["git-provider"]
)

unprotected_router.include_router(
    onboarding.router, prefix="/onboarding", tags=["onboarding"]
)

unprotected_router.include_router(
    subscription.router, prefix="/subscription", tags=["subscription"]
)

# /studio/v1/signup/** -------------------------------------------------
if settings.ENABLE_SIGNUP:
    unprotected_router.include_router(
        signup.router, prefix="/signup", tags=["signup"]
    )


# Optional local GraphQL sandbox --------------------------------------
if settings.ENVIRONMENT != "production":
    unprotected_router.include_router(
        sandbox_router, prefix="/sandbox", tags=["legacy-sandbox"]
    )

# Export symbol consumed by main.py
__all__ = ["unprotected_router"]
