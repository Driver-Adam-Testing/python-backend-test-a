#!/usr/bin/env python3
"""
Fetch historical Auth0 logs and format them for event processor testing.

This tool fetches logs from the Auth0 Management API and transforms them into
the EventBridge event format expected by the event processor.
"""

import argparse
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


class Auth0LogFetcher:
    """Fetches historical logs from Auth0 Management API."""

    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    def _get_management_token(self) -> str:
        """Get a Management API access token."""
        if self._token and self._token_expires_at:
            if datetime.now(UTC) < self._token_expires_at:
                return self._token

        url = f"https://{self.domain}/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": f"https://{self.domain}/api/v2/",
            "grant_type": "client_credentials",
        }

        response = httpx.post(url, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        self._token = data["access_token"]
        expires_in = data.get("expires_in", 86400)
        self._token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in - 60)

        return self._token

    def fetch_logs(
        self,
        event_types: list[str] | None = None,
        from_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Fetch logs from Auth0 Management API.

        Args:
            event_types: List of event type codes to filter (e.g., ['s', 'ss', 'sdu'])
            from_date: Fetch logs from this date onwards
            limit: Maximum number of logs to fetch

        Returns:
            List of raw Auth0 log entries
        """
        token = self._get_management_token()
        url = f"https://{self.domain}/api/v2/logs"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        params: dict[str, Any] = {
            "per_page": min(limit, 100),
            "sort": "date:-1",
        }

        # Build Lucene query for filtering
        query_parts = []

        if from_date:
            # Format: date:[2025-01-01T00:00:00.000Z TO *]
            date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            query_parts.append(f"date:[{date_str} TO *]")

        if event_types:
            # Format: type:(s OR ss OR sdu)
            type_query = " OR ".join(event_types)
            query_parts.append(f"type:({type_query})")

        if query_parts:
            params["q"] = " AND ".join(query_parts)

        all_logs = []
        fetched = 0

        while fetched < limit:
            logger.info(f"Fetching logs (batch size: {params['per_page']})")
            response = httpx.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            logs = response.json()
            if not logs:
                break

            all_logs.extend(logs)
            fetched += len(logs)

            logger.info(f"Fetched {len(logs)} logs (total: {len(all_logs)})")

            # Check if we have more logs to fetch
            if len(logs) < params["per_page"]:
                break

            # Update from parameter to fetch next page (using log_id for pagination)
            if logs:
                last_log_id = logs[-1]["log_id"]
                params["from"] = last_log_id

            if fetched >= limit:
                break

        return all_logs[:limit]


def transform_log_to_eventbridge_event(log: dict[str, Any]) -> dict[str, Any]:
    """
    Transform Auth0 log entry into EventBridge event format.

    Auth0 logs have a different structure than EventBridge events.
    This function maps the Auth0 log format to the expected EventBridge format.
    """
    event_type = log.get("type", "unknown")
    user_id = log.get("user_id")
    organization_id = log.get("organization_id")
    log_id = log.get("log_id")

    # Build the EventBridge event structure
    eventbridge_event = {
        "id": log_id,
        "source": "aws.partner/auth0.com",
        "detail-type": "Auth0 log event",
        "time": log.get("date", datetime.now(UTC).isoformat()),
        "detail": {
            "log_id": log_id,
            "data": {
                "type": event_type,
                "user_id": user_id,
                "organization_id": organization_id,
                "details": log.get("details", {}),
            },
        },
    }

    return eventbridge_event


def save_events_for_testing(
    events: list[dict[str, Any]],
    output_path: str,
) -> None:
    """
    Save events in the format expected by test_auth0_events.py.

    The test script expects an array of objects with a "message" field
    containing the JSON-serialized event.
    """
    wrapped_events = [{"message": json.dumps(event)} for event in events]

    with open(output_path, "w") as f:
        json.dump(wrapped_events, f, indent=2)

    logger.info(f"Saved {len(events)} events to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch historical Auth0 logs for event processor testing"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="auth0_test_events.json",
        help="Output file path (default: auth0_test_events.json)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=100,
        help="Maximum number of logs to fetch (default: 100)",
    )
    parser.add_argument(
        "-t",
        "--types",
        nargs="+",
        help="Event types to filter (e.g., s ss sdu organization_member_added)",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=7,
        help="Fetch logs from the last N days (default: 7)",
    )
    parser.add_argument(
        "--from-date",
        help="Fetch logs from this date (ISO format: YYYY-MM-DD)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Determine date range
    if args.from_date:
        from_date = datetime.fromisoformat(args.from_date).replace(tzinfo=UTC)
    else:
        from_date = datetime.now(UTC) - timedelta(days=args.days)

    logger.info(f"Fetching logs from {from_date.isoformat()}")
    if args.types:
        logger.info(f"Filtering event types: {args.types}")

    # Initialize fetcher
    fetcher = Auth0LogFetcher(
        domain=settings.AUTH0_MGMT_API_DOMAIN,
        client_id=settings.AUTH0_MGMT_API_CLIENT_ID,
        client_secret=settings.AUTH0_MGMT_API_CLIENT_SECRET,
    )

    # Fetch logs
    logger.info("Fetching logs from Auth0...")
    logs = fetcher.fetch_logs(
        event_types=args.types,
        from_date=from_date,
        limit=args.limit,
    )

    logger.info(f"Fetched {len(logs)} logs from Auth0")

    # Count event types
    event_type_counts: dict[str, int] = {}
    for log in logs:
        event_type = log.get("type", "unknown")
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

    logger.info("Event type distribution:")
    for event_type, count in sorted(event_type_counts.items()):
        logger.info(f"  {event_type}: {count}")

    # Transform to EventBridge format
    logger.info("Transforming logs to EventBridge format...")
    events = [transform_log_to_eventbridge_event(log) for log in logs]

    # Save to file
    save_events_for_testing(events, args.output)

    print(f"\n✅ Successfully saved {len(events)} events to {args.output}")
    print(f"\nTo test these events, run:")
    print(f"  python -m src.event_processor.test_auth0_events {args.output}")


if __name__ == "__main__":
    main()