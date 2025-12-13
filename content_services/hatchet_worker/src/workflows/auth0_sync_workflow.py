from datetime import timedelta

from auth0_sync.src.main import sync_auth0
from hatchet_client import hatchet
from hatchet_sdk import Context
from shared.interfaces.hatchet_interfaces import (
    Auth0SyncInput,
    ProcessAuth0EventInput,
)

# TODO: scheduled auth0_sync


@hatchet.task(name="auth0-sync-workflow", execution_timeout=timedelta(minutes=60))
def auth0_sync_task(input: Auth0SyncInput, ctx: Context) -> dict:
    print("starting auth0 sync task")
    result = sync_auth0(
        dry_run=input.dry_run,
        verbose=input.verbose,
        initial_run=input.initial_run,
    )
    print("executed auth0 sync task")
    return result


@hatchet.task(
    name="process-auth0-event-workflow", execution_timeout=timedelta(minutes=15)
)
def process_auth0_event_task(input: ProcessAuth0EventInput, ctx: Context) -> dict:
    print("starting process auth0 event task")
    from auth0_sync.src.main import process_auth0_events

    result = process_auth0_events(event=input.event)
    print("executed process auth0 event task")
    return result


@hatchet.task(
    name="scheduled-auth0-sync-workflow",
    execution_timeout=timedelta(minutes=60),
    on_crons=["0 2 * * *"],
)
def scheduled_auth0_sync_task(ctx: Context) -> dict:
    print("starting scheduled auth0 sync task")
    result = sync_auth0(
        dry_run=False,
        verbose=False,
        initial_run=False,
    )
    print("executed scheduled auth0 sync task")
    return result
