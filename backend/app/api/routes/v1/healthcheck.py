from fastapi import APIRouter
from pydantic import BaseModel
import os

router = APIRouter()


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK" + " git_commit:" +  os.getenv("GIT_COMMIT", "unknown") + " git_branch:" + os.getenv("GIT_BRANCH", "unknown")


@router.get(
    "/",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")


@router.get("/sentry-debug")
async def trigger_error() -> None:
    1 / 0  # noqa: B018
