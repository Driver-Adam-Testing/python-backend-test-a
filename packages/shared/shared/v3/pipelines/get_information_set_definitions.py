from pydantic import BaseModel
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.pipelines.interfaces.pipeline_request import PipelineExecutionRequest
from shared.v3.static.messages.pipeline_get_information_sets_definitions_messages import (
    GetInformationSetsParametersMessage,
    GetInformationSetsUserMessage,
    InformationSetsSystemMessage,
)
from shared.v3.static.response_types.get_information_set_definitions_llm_response import (
    InformationSetDefinitionList,
    InformationSetRetrievalParameters,
)


class DefineRetrievalSetsPipelineResponse(BaseModel):
    retrieval_sets: list[str]


def get_information_set_definitions(
    pipeline_execution_request: PipelineExecutionRequest,
) -> dict:
    """
    This is a 2 step pipeline:
    1. Get all the sets that need to be retrieved.
    2. Determine retrieval methods for each set.
    """
    llm_client = LlmClient.from_config(LlmConfig.from_name("o3_mini"))
    information_sets_step_1 = llm_client.generate(
        response_type=InformationSetDefinitionList,
        message_history=LlmMessageHistory(
            messages=[
                InformationSetsSystemMessage(),
                GetInformationSetsUserMessage.from_context(
                    prompt=pipeline_execution_request.original_prompt,
                    page_content_before_cursor=pipeline_execution_request.text_before_selection,
                    selected_text=pipeline_execution_request.selected_text,
                ),
            ]
        ),
    ).parsed_content

    def fetch_retrieval_parameters(
        information_set: any,
    ) -> InformationSetRetrievalParameters:
        return llm_client.generate(
            response_type=InformationSetRetrievalParameters,
            message_history=LlmMessageHistory(
                messages=[
                    InformationSetsSystemMessage(),
                    GetInformationSetsParametersMessage.from_context(
                        prompt=pipeline_execution_request.original_prompt,
                        information_set_name=information_set.name,
                        information_set_description=information_set.description,
                        information_set_rationale=information_set.rationale,
                        selected_text=pipeline_execution_request.selected_text,
                    ),
                ]
            ),
        ).parsed_content

    information_sets_with_parameters = []

    for information_set in information_sets_step_1.information_sets:
        information_set_retrieval_parameters = fetch_retrieval_parameters(
            information_set
        )
        information_sets_with_parameters.append(
            {
                "information_set": information_set,
                "parameters": information_set_retrieval_parameters,
            }
        )

    return {"information_sets_with_parameters": information_sets_with_parameters}
