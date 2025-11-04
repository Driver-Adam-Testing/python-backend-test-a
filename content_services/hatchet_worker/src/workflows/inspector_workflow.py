import asyncio
from datetime import timedelta

from hatchet_client import hatchet
from hatchet_sdk import Context
from inspector.src.main import inspect_db
from pydantic import BaseModel
from shared.inspector.utils.dag import LiteNode


class InspectorInput(BaseModel):
    version_id: str


class TechDocInput(BaseModel):
    node: LiteNode
    codebase_name: str
    source_code: str
    version_id: str


@hatchet.task(name="inspector-workflow", execution_timeout=timedelta(minutes=60))
def inspector_task(input: InspectorInput, ctx: Context) -> dict[str, str]:
    print("starting inspector task")
    asyncio.run(inspect_db(input.version_id))
    print("executed inspector task")
    return {"status": "inspection complete"}
