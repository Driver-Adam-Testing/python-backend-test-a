from datetime import timedelta

from autodocs.src.main import run_autodoc
from database.models_enums import AutoDocConfigKind, ContentKind
from hatchet_client import hatchet
from hatchet_sdk import Context
from pydantic import BaseModel


class AutodocInput(BaseModel):
    page_node_id: str
    config_kind: AutoDocConfigKind
    document_goal: str | None
    user_context: str | None
    content_kind: ContentKind | None


@hatchet.task(name="autodocs-workflow", execution_timeout=timedelta(minutes=480))
async def autodocs_task(input: AutodocInput, ctx: Context) -> dict[str, str]:
    print("starting autodocs task")
    await run_autodoc(
        page_node_id=input.page_node_id,
        config_kind=input.config_kind,
        document_goal=input.document_goal,
        user_context=input.user_context,
        content_kind=input.content_kind,
    )
    print("executed autodocs task")
    return {"result": "autodoc completed"}
