import random
import string
import uuid

from database.models_v1 import Workspace


def random_workspace(organization_id: str | None = None):
    random_display_name = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=10)
    )
    random_description = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=20)
    )
    workspace = Workspace(
        id=uuid.uuid4(),
        display_name=random_display_name,
        description=random_description,
    )
    if organization_id:
        workspace.organization_id = organization_id
    return workspace
