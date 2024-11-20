"""
A simple client to send events to the metrics handler
"""

import json
from datetime import datetime

import boto3


def send_event(
    detail_type: str,
    detail: dict,
    resources: list = None,
    session_id: str = None,
    endpoint_id: str = None,
):
    client = boto3.client("events", region_name="us-east-1")

    entry = {
        "Time": datetime.now(),
        "Source": "metrics.client",
        "DetailType": detail_type,
        "Detail": json.dumps(detail),  # Convert detail dict to JSON string
        "EventBusName": "metrics-event-bus",
    }

    # Optional fields
    if resources:
        entry["Resources"] = resources
    if session_id:
        entry["TraceHeader"] = session_id

    try:
        # Send the event
        response = client.put_events(
            Entries=[entry],
            # EndpointId=endpoint_id  # Include endpoint ID if provided
        )
        return response
    except Exception as e:
        print(f"Error sending event: {e}")
        raise


def main():
    detail = {"event": "test", "data": "test"}

    resp = send_event(detail_type="inspector_tech_doc_usage_debit", detail=detail)
    print(resp)


if __name__ == "__main__":
    main()
