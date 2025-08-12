import logging
from datetime import datetime

from app.auth.api_key_common import create_api_key_payload
from app.auth.async_cache import AsyncTTLCache
from app.services.auth0_async import AsyncAuth0Service
from database.db import async_engine
from database.models_v2 import ApiKey
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

# Cache for API key verification results (10 minutes TTL to match sync version)
_api_key_cache = AsyncTTLCache(ttl=600, max_size=1000)

# Cache for org membership checks (1 hour TTL)
_org_membership_cache = AsyncTTLCache(ttl=3600, max_size=1000)


async def _is_member_of_org_async(
    user_id: str, org_id: str, auth0_service: AsyncAuth0Service
) -> bool:
    """
    Async version of org membership check with caching.
    """
    cache_key = f"{user_id}:{org_id}"

    cached = await _org_membership_cache.get(cache_key)
    if cached is not None:
        return cached

    orgs_data = await auth0_service.list_user_organizations_async(user_id)
    organizations = orgs_data.get("organizations", [])
    is_member = any(o["id"] == org_id for o in organizations)

    await _org_membership_cache.set(cache_key, is_member)

    return is_member


async def verify_api_key_async(raw_key: str, auth0_service: AsyncAuth0Service) -> dict:
    """
    Async version of verify_api_key that returns identical results.
    """
    cached_result = await _api_key_cache.get(raw_key)
    if cached_result:
        return cached_result

    async with AsyncSession(async_engine) as session:
        statement = select(ApiKey).where(ApiKey.key == raw_key)
        result = await session.exec(statement)
        api_key = result.one_or_none()

        if not api_key:
            raise HTTPException(401, "Invalid API key")

        if not await _is_member_of_org_async(
            api_key.user_id, api_key.organization_id, auth0_service
        ):
            raise HTTPException(401, "User does not belong to this organization")

        # TODO change back after Neil's fix to db column type
        api_key.last_used_at = datetime.now()  # datetime.now(ZoneInfo("UTC"))
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)

        # Create payload within the session context
        payload = create_api_key_payload(api_key)

    await _api_key_cache.set(raw_key, payload)

    return payload
