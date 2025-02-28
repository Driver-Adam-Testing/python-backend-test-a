from pydantic import BaseModel
from shared.interfaces.agents.data_scope import DataScope


class PipelineExecutionRequest(BaseModel):
    original_prompt: str
    selected_text: str | None = None
    text_before_selection: str | None = None
    text_after_selection: str | None = None
    datascope: DataScope
