from pydantic import BaseModel
from shared.v3.utils.references import Reference, ReferenceSet


class PipelineResponse(BaseModel):
    """
    A response from a pipeline.
    """

    final_response: str
    references: list[Reference]

    # Todo: Add a from_llm_session or message_history constructor
    def __init__(self, **data: dict[str, any]) -> None:
        if isinstance(data.get("references"), list):
            data["references"] = ReferenceSet(references=set(data["references"]))
        super().__init__(**data)
