#!/usr/bin/env python3
"""Test script for Auth0 event processing with real events."""

import json
import logging

from app.iam.auth0_event_processor_test import test_event_with_logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_events_from_file(file_path: str) -> None:
    try:
        with open(file_path) as f:
            events_data = json.load(f)

        # Handle the format from test.json (array of event wrapper objects)
        events_to_process = []
        for event_wrapper in events_data:
            if "message" in event_wrapper:
                event_dict = json.loads(event_wrapper["message"])
                events_to_process.append(event_dict)

        print(f"Loaded {len(events_to_process)} events from {file_path}")

        # Group events by type for summary
        event_types = {}
        for event_dict in events_to_process:
            event_type = (
                event_dict.get("detail", {}).get("data", {}).get("type", "unknown")
            )
            event_types[event_type] = event_types.get(event_type, 0) + 1

        print(f"Event types found: {dict(event_types)}")

        # Process each event
        successful_events = 0
        failed_events = 0

        for i, event_dict in enumerate(events_to_process, 1):
            event_type = (
                event_dict.get("detail", {}).get("data", {}).get("type", "unknown")
            )
            _log_id = event_dict.get("detail", {}).get("log_id", "no-log-id")
            user_id = (
                event_dict.get("detail", {}).get("data", {}).get("user_id", "no-user")
            )
            org_id = (
                event_dict.get("detail", {})
                .get("data", {})
                .get("organization_id", "no-org")
            )

            print(f"\n{'=' * 80}")
            print(f"EVENT #{i}/{len(events_to_process)}: {event_type}")
            print(f"User: {user_id}, Org: {org_id}")
            print("=" * 80)

            try:
                result = test_event_with_logging(event_dict)

                if result["success"]:
                    successful_events += 1
                    print("✅ Event processed successfully!")
                    print("📊 Summary:")
                    print(
                        f"   - Event Type: {result['processing_result']['event_type']}"
                    )
                    print(
                        f"   - Entities Updated: {result['processing_result']['entities_updated']}"
                    )
                    print(
                        f"   - Database Operations: {result['summary']['operations_count']}"
                    )

                    if result["database_operations"]:
                        print("\n🔍 Database Operations:")
                        for j, op in enumerate(result["database_operations"], 1):
                            if op["action"] in ["INSERT", "UPDATE", "DELETE"]:
                                print(f"   {j}. {op['action']} {op['table']}")
                                if op["data"] and op["action"] != "COMMIT":
                                    # Show key fields only
                                    key_fields = [
                                        "id",
                                        "email",
                                        "user_id",
                                        "org_id",
                                        "name",
                                    ]
                                    for key in key_fields:
                                        if key in op["data"]:
                                            print(f"      {key}: {op['data'][key]}")
                            else:
                                print(f"   {j}. {op['action']}")
                else:
                    failed_events += 1
                    print("❌ Event processing failed!")
                    if result["processing_result"].get("error"):
                        print(f"Error: {result['processing_result']['error']}")

            except Exception as e:
                failed_events += 1
                print(f"❌ Event failed to process: {e}")
                logger.error(f"Failed to process event #{i}", exc_info=True)

        print(f"\n{'=' * 80}")
        print("FINAL SUMMARY")
        print("=" * 80)
        print(f"Total events: {len(events_to_process)}")
        print(f"Successful: {successful_events}")
        print(f"Failed: {failed_events}")
        print("\nEvent type distribution:")
        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count}")

    except Exception as e:
        print(f"❌ Failed to load events from {file_path}: {e}")
        logger.error("Failed to load events from file", exc_info=True)


def main() -> None:
    import sys

    print("Auth0 Event Processing Test")
    print("Uses real Auth0 API with mocked database operations\n")

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Testing with events from file: {file_path}")
        test_events_from_file(file_path)
    else:
        print("Usage: python test_auth0_events.py /path/to/events.json")


if __name__ == "__main__":
    main()
