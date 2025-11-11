from database.models import Organization
from database.models_enums import SourceVisibility
from sqlmodel import Session


def get_default_source_visibility(
    session: Session, organization_id: str
) -> SourceVisibility:
    org = session.get(Organization, organization_id)
    if not org:
        raise ValueError(f"Organization {organization_id} not found")
    return org.default_source_visibility


def update_default_source_visibility(
    session: Session,
    organization_id: str,
    visibility: SourceVisibility,
) -> SourceVisibility:
    org = session.get(Organization, organization_id)
    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    org.default_source_visibility = visibility
    session.add(org)
    session.commit()
    session.refresh(org)
    return org.default_source_visibility
