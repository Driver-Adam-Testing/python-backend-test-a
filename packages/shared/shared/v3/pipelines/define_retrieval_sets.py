import enum

from pydantic import BaseModel
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message_history import LlmMessageHistory
from shared.v3.pipelines.interfaces.pipeline_request import PipelineExecutionRequest
from shared.v3.static.messages.driver_application_messages import (
    AgenticContextMessage,
    DriverApplicationMessage,
)
from shared.v3.utils.parseable import LlmParseable


class DefineRetrievalSetsPipelineResponse(BaseModel):
    retrieval_sets: list[str]


class RetrievalSets(LlmParseable):
    """
    This class encapsulates a collection of retrieval sets, each detailing the information to be retrieved, the retrieval instructions, and the scope of retrieval.

    Attributes:
        information_sets (list[InformationSet]): A list of InformationSet instances, each representing a distinct set of information to be retrieved.

    class InformationSet:
        Attributes:
            information_set (str): The specific information set to be retrieved.
            retrieval_instructions (str): Guidelines on how to retrieve the information set.
            information_set_type (InformationSetType): The classification of the information set to be retrieved.

    InformationSetType values:
        - "FINITE_SET_DEFINED_BY_KEYWORD_REFERENCE": Identifies information sets retrievable via specific keywords or references within the document.
        - "FINITE_SET_DEFINED_BY_ANALYTICAL_EXAMINATION": Pertains to information sets requiring detailed analysis or examination for retrieval.
        - "CONCEPTUAL_SET": Refers to conceptual set that cannot be halted during a search, necessitating a broader understanding or exploration for retrieval.
    """

    class InformationSet(LlmParseable):
        class InformationSetType(str, enum.Enum):
            FINITE_SET_DEFINED_BY_KEYWORD_REFERENCE = (
                "FINITE_SET_DEFINED_BY_KEYWORD_REFERENCE"
            )
            FINITE_SET_DEFINED_BY_ANALYTICAL_EXAMINATION = (
                "FINITE_SET_DEFINED_BY_ANALYTICAL_EXAMINATION"
            )
            CONCEPTUAL_SET = "CONCEPTUAL_SET"

        retrieval_instructions: str
        query_strings: list[str]
        information_set_type: InformationSetType

    information_sets: list[InformationSet]


def get_retrieval_instructions(
    pipeline_execution_request: PipelineExecutionRequest,
) -> list[dict]:
    """
    Get all the sets that need to be retrieved, either conceptual or keyword, and an instruction to retrieve them using the LlmClient o3_mini.

    Returns:
        list[dict]: A list of dictionaries, each containing a retrieval set and its corresponding instruction.
    """
    llm_client = LlmClient.from_config(LlmConfig.from_name("o3_mini"))

    prompt = f"""
    Given the user prompt: {pipeline_execution_request.original_prompt}
    within a document that contains the following text:
    {pipeline_execution_request.text_before_selection}

    <<<THIS IS WHERE THE USER IS>>>

    {pipeline_execution_request.text_after_selection}

    I need to retrieve information of external sets of information via search, file retrieval, file system examination, or other means.
    Please return a list of sets of information that I need to retrieve, and the instructions for retrieval.
    """

    return llm_client.generate(
        prompt=prompt,
        response_type=RetrievalSets,
        message_history=LlmMessageHistory(
            messages=[AgenticContextMessage(), DriverApplicationMessage()]
        ),
    ).parsed_content
