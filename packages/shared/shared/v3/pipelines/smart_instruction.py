from shared.interfaces.agents.data_scope import DataScope
from shared.v3.pipelines.compress_page_content import (
    compress_after,
    compress_before,
)
from shared.v3.pipelines.define_retrieval_sets import get_retrieval_instructions
from shared.v3.pipelines.interfaces.pipeline_request import PipelineExecutionRequest


def run_smart_instruction(
    user_prompt: str,
    text_before_instruction: str,
    text_after_instruction: str,
    datascope: DataScope,
) -> dict:
    abbreviated_before = compress_before(
        pipeline_execution_request=PipelineExecutionRequest(
            original_prompt=user_prompt,
            text_before_selection=text_before_instruction,
            text_after_selection=None,
            selected_text=None,
            datascope=datascope,
        )
    )

    abbreviated_after = compress_after(
        pipeline_execution_request=PipelineExecutionRequest(
            original_prompt=user_prompt,
            text_before_selection=None,
            text_after_selection=text_after_instruction,
            selected_text=None,
            datascope=datascope,
        )
    )

    retrieval_instructions = get_retrieval_instructions(
        pipeline_execution_request=PipelineExecutionRequest(
            original_prompt=user_prompt,
            text_before_selection=text_before_instruction,
            text_after_selection=text_after_instruction,
            selected_text=None,
            datascope=datascope,
        )
    )

    return {
        "abbreviated_before": abbreviated_before.abbreviated_document_text
        if abbreviated_before
        else "",
        "abbreviated_after": abbreviated_after.abbreviated_document_text
        if abbreviated_after
        else "",
        "retrieval_instructions": retrieval_instructions,
    }
