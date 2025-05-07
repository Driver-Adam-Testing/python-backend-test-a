from pydantic import BaseModel
from shared.v3.utils.post_processing.mermaid import fix_mermaid_syntax_in_response
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

        if "```mermaid" in data.get("final_response", ""):
            data["final_response"] = fix_mermaid_syntax_in_response(
                data["final_response"]
            )

        super().__init__(**data)
