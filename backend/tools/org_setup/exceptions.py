class OrgSetupError(Exception):
    """Base exception for organization setup failures."""


class Auth0SetupError(OrgSetupError):
    """Auth0 operation failure during setup."""


class DatabaseSetupError(OrgSetupError):
    """Database operation failure during setup."""


class RollbackError(OrgSetupError):
    """Failure during rollback/cleanup operations."""
