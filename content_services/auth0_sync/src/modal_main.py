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
def sync_auth0(
    dry_run: bool = False, verbose: bool = False, initial_run: bool = False
) -> dict:
    import logging

    from auth0_sync.sync import Auth0Sync

    logger = logging.getLogger(__name__)

    syncer = Auth0Sync(dry_run=dry_run, verbose=verbose)
    stats = syncer.run(initial_run=initial_run)

    logger.info(f"Sync completed with stats: {stats}")
    return stats


@app.function(min_containers=1, **function_config)
def process_auth0_events(event: dict) -> dict:
    import logging

    from event_processor.auth0_event_processor import process_auth0_event

    logger = logging.getLogger(__name__)

    logger.info(f"Processing Auth0 event: {event}")
    result = process_auth0_event(event)
    logger.info(f"Event processing result: {result}")
    return result.model_dump()


@app.local_entrypoint()
def main(
    dry_run: bool = False, verbose: bool = False, initial_run: bool = False
) -> None:
    """CLI entrypoint for manual Auth0 sync.

    Usage:
        modal run src/modal_main.py --dry-run --verbose
    """
    print("Starting Auth0 sync...")
    print(f"Dry run: {dry_run}, Verbose: {verbose}, Initial run: {initial_run}")
    result = sync_auth0.remote(
        dry_run=dry_run, verbose=verbose, initial_run=initial_run
    )
    print(f"\nSync completed. Stats: {result}")
