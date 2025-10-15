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



ORG_MEMBER_DELETED_EVENT = {'version': '0', 'id': 'c2efdc54-030d-e6c7-ef97-7189dbc7fc14', 'detail-type': 'Auth0 log', 'source': 'aws.partner/auth0.com/driverai-dev-5b4b5f6f-32b8-4df4-9c1c-cf5f04c1bbb4/auth0.logs', 'account': '550082761109', 'time': '2025-10-15T06:54:28Z', 'region': 'us-east-1', 'resources': [], 'detail': {'log_id': '90020251015065428081171000000000000001223372090939918132', 'data': {'date': '2025-10-15T06:54:28.059Z', 'type': 'sapi', 'description': 'Delete a User', 'client_id': '8uKCXVNdM5FBlWQhuXjsEd5CEkb42jd9', 'client_name': '', 'ip': '2600:1700:1971:8430:4860:9341:d1ac:2f55', 'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', 'details': {'request': {'method': 'delete', 'path': '/api/v2/users/auth0%7C68ef4292aee8a61d14791224', 'query': {}, 'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', 'body': {}, 'channel': 'https://manage.auth0.com/', 'ip': '2600:1700:1971:8430:4860:9341:d1ac:2f55', 'auth': {'user': {'user_id': 'google-oauth2|116967649572818180860', 'name': 'Eric Miller', 'email': 'eric.miller@driverai.com'}, 'strategy': 'jwt', 'credentials': {'jti': 'e64c9317199e1aed9ee983a094afdbc7', 'scopes': ['create:actions', 'create:authentication_methods', 'create:client_credentials', 'create:client_grants', 'create:clients', 'create:connection_profiles', 'create:connections', 'create:connections_keys', 'create:custom_domains', 'create:email_provider', 'create:email_templates', 'create:event_streams', 'create:guardian_enrollment_tickets', 'create:integrations', 'create:log_streams', 'create:network_acls', 'create:organization_client_grants', 'create:organization_connections', 'create:organization_discovery_domains', 'create:organization_invitations', 'create:organization_member_roles', 'create:organization_members', 'create:organizations', 'create:phone_providers', 'create:phone_templates', 'create:resource_servers', 'create:roles', 'create:rules', 'create:scim_config', 'create:scim_token', 'create:self_service_profiles', 'create:shields', 'create:signing_keys', 'create:sso_access_tickets', 'create:tenant_invitations', 'create:test_email_dispatch', 'create:user_attribute_profiles', 'create:users', 'create:vdcs_templates', 'delete:actions', 'delete:anomaly_blocks', 'delete:authentication_methods', 'delete:branding', 'delete:client_credentials', 'delete:client_grants', 'delete:clients', 'delete:connection_profiles', 'delete:connections', 'delete:custom_domains', 'delete:device_credentials', 'delete:email_provider', 'delete:email_templates', 'delete:event_streams', 'delete:grants', 'delete:guardian_enrollments', 'delete:integrations', 'delete:log_streams', 'delete:network_acls', 'delete:organization_client_grants', 'delete:organization_connections', 'delete:organization_discovery_domains', 'delete:organization_invitations', 'delete:organization_member_roles', 'delete:organization_members', 'delete:organizations', 'delete:owners', 'delete:phone_providers', 'delete:phone_templates', 'delete:resource_servers', 'delete:roles', 'delete:rules', 'delete:rules_configs', 'delete:scim_config', 'delete:scim_token', 'delete:self_service_profiles', 'delete:shields', 'delete:tenant_invitations', 'delete:tenant_members', 'delete:tenants', 'delete:user_attribute_profiles', 'delete:users', 'delete:vdcs_templates', 'read:actions', 'read:anomaly_blocks', 'read:attack_protection', 'read:authentication_methods', 'read:branding', 'read:checks', 'read:client_credentials', 'read:client_grants', 'read:client_keys', 'read:clients', 'read:connection_profiles', 'read:connections', 'read:connections_keys', 'read:connections_options', 'read:custom_domains', 'read:device_credentials', 'read:email_provider', 'read:email_templates', 'read:entity_counts', 'read:event_deliveries', 'read:event_streams', 'read:grants', 'read:groups', 'read:guardian_factors', 'read:insights', 'read:integrations', 'read:log_streams', 'read:logs', 'read:mfa_policies', 'read:network_acls', 'read:organization_client_grants', 'read:organization_connections', 'read:organization_discovery_domains', 'read:organization_invitations', 'read:organization_member_roles', 'read:organization_members', 'read:organizations', 'read:phone_providers', 'read:phone_templates', 'read:prompts', 'read:resource_servers', 'read:roles', 'read:rules', 'read:rules_configs', 'read:scim_config', 'read:scim_token', 'read:self_service_profile_custom_texts', 'read:self_service_profiles', 'read:shields', 'read:signing_keys', 'read:stats', 'read:tenant_invitations', 'read:tenant_members', 'read:tenant_settings', 'read:triggers', 'read:user_attribute_profiles', 'read:users', 'read:vdcs_templates', 'run:checks', 'update:actions', 'update:attack_protection', 'update:authentication_methods', 'update:branding', 'update:client_credentials', 'update:client_grants', 'update:client_keys', 'update:clients', 'update:connection_profiles', 'update:connections', 'update:connections_keys', 'update:connections_options', 'update:custom_domains', 'update:email_provider', 'update:email_templates', 'update:event_deliveries', 'update:event_streams', 'update:guardian_factors', 'update:integrations', 'update:log_streams', 'update:mfa_policies', 'update:network_acls', 'update:organization_connections', 'update:organization_discovery_domains', 'update:organizations', 'update:phone_providers', 'update:phone_templates', 'update:prompts', 'update:resource_servers', 'update:roles', 'update:rules', 'update:rules_configs', 'update:scim_config', 'update:self_service_profile_custom_texts', 'update:self_service_profiles', 'update:shields', 'update:signing_keys', 'update:tenant_members', 'update:tenant_settings', 'update:triggers', 'update:user_attribute_profiles', 'update:users', 'update:vdcs_templates']}}}, 'response': {'statusCode': 204, 'body': {}}}, 'user_id': 'google-oauth2|116967649572818180860', '$event_schema': {'version': '1.0.0'}, 'environment_name': 'prod-us-4', 'log_id': '90020251015065428081171000000000000001223372090939918132', 'tenant_name': 'driverai-dev'}}}


if __name__ == "__main__":
    # process_auth0_events_local(ORG_MEMBER_ADDED_EVENT)
    process_auth0_events_local(ORG_MEMBER_DELETED_EVENT)