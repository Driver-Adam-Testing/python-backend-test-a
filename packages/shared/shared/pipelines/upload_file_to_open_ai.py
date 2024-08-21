import io
import os

import requests
from database.models_v1 import ContentMetadata, ContentType
from openai import OpenAI
from sqlmodel import Session, create_engine


def upload_file_to_open_ai(
    workspace: str, file_content: bytes, codebase_id: str = None, url: str = None
) -> str:
    client = OpenAI()
    file_io = io.BytesIO(file_content)

    # TODO: move away from this functionality.

    file_io.name = "auxiliary_document.pdf"
    uploaded_file = client.files.create(
        file=file_io,
        purpose="assistants",
    )

    engine = create_engine(os.environ["DATABASE_URL"], pool_size=1, max_overflow=10)

    with Session(engine) as session:
        session.add(
            ContentMetadata(
                workspace_id=workspace,
                codebase_id=codebase_id,
                content_type=ContentType.AUXILIARY_DOCUMENTATION,
                misc_metadata={"file_id": uploaded_file.id, "url": url},
            )
        )
        session.commit()

    return uploaded_file.id


def upload_file_from_url_to_open_ai(
    workspace_id: str, file_url: str, codebase_id: str = None
) -> str:
    response = requests.get(file_url)
    response.raise_for_status()

    return upload_file_to_open_ai(
        workspace_id, response.content, codebase_id, url=file_url
    )
