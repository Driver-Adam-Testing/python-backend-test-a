import logging

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")


def sync_auth0_scheduled() -> dict:
    """Scheduled Auth0 sync job - runs nightly at 2am UTC, 7pm PT."""
    import logging

    from .auth0_sync.sync import Auth0Sync

    logger = logging.getLogger(__name__)

    syncer = Auth0Sync(dry_run=False, verbose=False)
    stats = syncer.run()

    logger.info(f"Sync completed with stats: {stats}")
    return stats


def sync_auth0(
    dry_run: bool = False, verbose: bool = False, initial_run: bool = False
) -> dict:
    import logging

    from .auth0_sync.sync import Auth0Sync

    logger = logging.getLogger(__name__)

    syncer = Auth0Sync(dry_run=dry_run, verbose=verbose)
    stats = syncer.run(initial_run=initial_run)

    logger.info(f"Sync completed with stats: {stats}")
    return stats


def process_auth0_events(event: dict) -> dict:
    import logging

    from .event_processor.auth0_event_processor import process_auth0_event

    logger = logging.getLogger(__name__)

    logger.info(f"Processing Auth0 event: {event}")
    result = process_auth0_event(event)
    logger.info(f"Event processing result: {result}")
    return result.model_dump()
