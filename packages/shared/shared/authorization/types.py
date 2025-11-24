from enum import Enum


class AssignmentType(str, Enum):
    """Type of assignment for a user's role on an asset."""

    DIRECT = "direct"
    INHERITED = "inherited"
