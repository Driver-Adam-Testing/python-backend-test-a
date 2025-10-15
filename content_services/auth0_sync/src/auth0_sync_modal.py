import logging
import os

import modal

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_dir(local_path="../../driver_db", remote_path="/driver_db", copy=True)
    .add_local_dir(
        local_path="../../packages/shared", remote_path="/shared_pkg", copy=True
    )
    .pip_install(
        [
            "/driver_db",
            "/shared_pkg",
        ]
    )
    .add_local_python_source(
        "auth0_sync",
        copy=True,
    )
    .add_local_python_source(
        "event_processor",
        copy=True,
    )
    .add_local_python_source(
        "config",
        copy=True,
    )
)

app = modal.App("auth0_sync")

function_config = {
    "image": image,
    "secrets": [
        modal.Secret.from_name("db"),
        modal.Secret.from_name("auth0"),
    ],
    "proxy": modal.Proxy.from_name("my-proxy")
    if os.environ.get("MODAL_ENVIRONMENT") in ["dev", "staging"]
    else modal.Proxy.from_name("my-proxy", environment_name="prod"),
    "memory": 2048,
    "timeout": 7200,  # 2 hours
    "region": "us-east",
}


@app.function(schedule=modal.Cron("0 2 * * *"), **function_config)
def sync_auth0_scheduled() -> dict:
    """Scheduled Auth0 sync job - runs nightly at 2am UTC, 7pm PT."""
    import logging

    from auth0_sync.sync import Auth0Sync

    logger = logging.getLogger(__name__)

    syncer = Auth0Sync(dry_run=False, verbose=False)
    stats = syncer.run()

    logger.info(f"Sync completed with stats: {stats}")
    return stats


@app.function(**function_config)
def sync_auth0(dry_run: bool = False, verbose: bool = False) -> dict:
    import logging

    from auth0_sync.sync import Auth0Sync

    logger = logging.getLogger(__name__)

    syncer = Auth0Sync(dry_run=dry_run, verbose=verbose)
    stats = syncer.run()

    logger.info(f"Sync completed with stats: {stats}")
    return stats


@app.function(**function_config)
def process_auth0_events(event:dict) -> dict:
    print(event)
    from event_processor.auth0_event_processor import process_auth0_event
    result = process_auth0_event(event)
    print(result)
    return result.model_dump()

def process_auth0_events_local(event:dict) -> dict:
    print(event)
    from event_processor.auth0_event_processor import process_auth0_event
    result = process_auth0_event(event)
    print(result)
    return result.model_dump()

@app.local_entrypoint()
def main(dry_run: bool = False, verbose: bool = False) -> None:
    """CLI entrypoint for manual Auth0 sync.

    Usage:
        modal run src/auth0_sync_modal.py --dry-run --verbose
    """
    result = sync_auth0.remote(dry_run=dry_run, verbose=verbose)
    print(f"\nSync completed. Stats: {result}")



ORG_MEMBER_DELETED_EVENT = {'version': '0', 'id': 'd72bb5e8-f611-9324-7749-7a1e8ed2c084', 'detail-type': 'Auth0 log', 'source': 'aws.partner/auth0.com/driverai-dev-5b4b5f6f-32b8-4df4-9c1c-cf5f04c1bbb4/auth0.logs', 'account': '550082761109', 'time': '2025-10-14T18:24:45Z', 'region': 'us-east-1', 'resources': [], 'detail': {'log_id': '90020251014182445782836000000000000001223372090888748570', 'data': {'date': '2025-10-14T18:24:45.755Z', 'type': 'sapi', 'description': 'Delete members from an organization', 'client_id': '8uKCXVNdM5FBlWQhuXjsEd5CEkb42jd9', 'client_name': '', 'ip': '2600:1700:1971:8430:4860:9341:d1ac:2f55', 'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', 'details': {'request': {'method': 'delete', 'path': '/api/v2/organizations/org_zNbdjuOUhbcysAqK/members', 'query': {}, 'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', 'body': {'members': ['auth0|68ee858cc6698f34e7620c59']}, 'channel': 'https://manage.auth0.com/', 'ip': '2600:1700:1971:8430:4860:9341:d1ac:2f55', 'auth': {'user': {'user_id': 'google-oauth2|116967649572818180860', 'name': 'Eric Miller', 'email': 'eric.miller@driverai.com'}, 'strategy': 'jwt', 'credentials': {'jti': '6430c7a09501694cfb6b670f91025362'}}}, 'response': {'statusCode': 204, 'body': {}}}, 'user_id': 'google-oauth2|116967649572818180860', '$event_schema': {'version': '1.0.0'}, 'environment_name': 'prod-us-4', 'log_id': '90020251014182445782836000000000000001223372090888748570', 'tenant_name': 'driverai-dev'}}}
ORG_MEMBER_ADDED_EVENT = {'version': '0', 'id': 'b8759e66-ecff-c36d-8a0d-5342f5c03af4', 'detail-type': 'Auth0 log', 'source': 'aws.partner/auth0.com/driverai-dev-5b4b5f6f-32b8-4df4-9c1c-cf5f04c1bbb4/auth0.logs', 'account': '550082761109', 'time': '2025-10-14T18:15:58Z', 'region': 'us-east-1', 'resources': [], 'detail': {'log_id': '90020251014181558941147000000000000001223372090887881367', 'data': {'date': '2025-10-14T18:15:58.881Z', 'type': 'organization_member_added', 'description': 'Successfully added member to organization', 'connection': 'Username-Password-Authentication', 'connection_id': 'con_p678LcvvdbeDAmDA', 'client_id': 'JC322sFMG3tV3HePhJjtvDzRsnH12AsI', 'client_name': 'driver-ai-dev', 'ip': '2600:1700:1971:8430:4860:9341:d1ac:2f55', 'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', 'details': {'reason': 'invitation'}, 'hostname': 'auth.dev.driverai.com', 'user_id': '68ee858cc6698f34e7620c59', 'user_name': 'eric.miller+dev2@driverai.com', 'organization_id': 'org_zNbdjuOUhbcysAqK', 'organization_name': 'jesse-test-org', '$event_schema': {'version': '1.0.0'}, 'environment_name': 'prod-us-4', 'log_id': '90020251014181558941147000000000000001223372090887881367', 'tenant_name': 'driverai-dev'}}}



if __name__ == "__main__":
    # process_auth0_events_local(ORG_MEMBER_ADDED_EVENT)
    process_auth0_events_local(ORG_MEMBER_DELETED_EVENT)