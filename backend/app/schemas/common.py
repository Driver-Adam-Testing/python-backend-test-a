"""Common schema utilities and validators."""

from database.models_enums import SourceVisibility


def validate_visibility_not_public(v: SourceVisibility) -> SourceVisibility:
    """Validate that visibility is not public (not yet supported)."""
    if v == SourceVisibility.public:
        raise ValueError("Public visibility is not yet supported")
    return v
