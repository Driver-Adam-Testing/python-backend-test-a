import os

import requests
from database.models_v1 import ContentMetadata, ContentType
from sqlmodel import Session, create_engine

from packages.shared.shared.utils.openai_file import (
    upload_file_to_open_ai as upload_file,
)


def upload_file_to_open_ai(
    workspace: str, file_content: bytes, codebase_id: str = None, url: str = None
) -> str:
    file_id = upload_file(file_content=file_content)

    engine = create_engine(os.environ["DATABASE_URL"], pool_size=1, max_overflow=10)

    with Session(engine) as session:
        session.add(
            ContentMetadata(
                workspace_id=workspace,
                codebase_id=codebase_id,
                content_type=ContentType.AUXILIARY_DOCUMENTATION,
                misc_metadata={"file_id": file_id, "url": url},
            )
        )
        session.commit()

    return file_id


def upload_file_from_url_to_open_ai(
    workspace_id: str, file_url: str, codebase_id: str = None
) -> str:
    response = requests.get(file_url)
    response.raise_for_status()

    return upload_file_to_open_ai(
        workspace_id, response.content, codebase_id, url=file_url
    )
