from datetime import timedelta

from hatchet_client import hatchet
from hatchet_sdk import Context
from inspector.src.main import inspect_db
from pydantic import BaseModel


class InspectorInput(BaseModel):
    version_id: str


@hatchet.task(name="inspector-workflow", execution_timeout=timedelta(minutes=720))
async def inspector_task(input: InspectorInput, ctx: Context) -> dict[str, str]:
    print("starting inspector task")
    await inspect_db(input.version_id)
    print("executed inspector task")
    return {"status": "inspection complete"}
