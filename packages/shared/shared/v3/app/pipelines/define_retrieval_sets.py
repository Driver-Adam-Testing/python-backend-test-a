import enum

from pydantic import BaseModel
from shared.v3.app.pipelines.interfaces.pipeline_request import PipelineExecutionRequest
from shared.v3.app.static.messages.driver_app_messages import (
    AgenticContextMessage,
    DriverApplicationMessage,
)
from shared.v3.interfaces.llm_parseable import LlmParseable
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message_history import LlmMessageHistory


class DefineRetrievalSetsPipelineResponse(BaseModel):
    retrieval_sets: list[str]


class RetrievalSets(LlmParseable):
    """
    This class encapsulates a collection of retrieval sets, each detailing the information to be retrieved, the retrieval instructions, and the scope of retrieval.

    Attributes:
        information_sets (list[InformationSet]): A list of InformationSet instances, each representing a distinct set of information to be retrieved.

    class InformationSet:
        Attributes:
            query_strings: list[str]: keywords, conceptual queries, or analytical queries that will be used to retrieve the information set.
            retrieval_instructions (str): Guidelines on how to retrieve the information set. Under 20 words.
            information_set_type (InformationSetType): The classification of the information set to be retrieved.

    InformationSetType values:
        - "FINITE_SET_DEFINED_BY_EXACT_KEYWORD_MATCH": Identifies information sets retrievable via exact keywords. e.g. function names, variable names, class names, etc.
        - "FINITE_SET_DEFINED_BY_ANALYTICAL_EXAMINATION": Pertains to information sets who's retrieval requires analysis of the context or intention of the information. e.g. functions that throw exceptions, operations that call i/o, string manipulation, authentication mechanisms, etc.
        - "CONCEPTUAL_SET": Refers to conceptual set that cannot be halted during a search, necessitating a broader understanding or exploration for retrieval. e.g. architecure information, design patterns, business logic, etc.
    """

    class InformationSet(LlmParseable):
        class InformationSetType(str, enum.Enum):
            FINITE_SET_DEFINED_BY_EXACT_KEYWORD_MATCH = (
                "FINITE_SET_DEFINED_BY_EXACT_KEYWORD_MATCH"
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
) -> RetrievalSets:
    """
    This is a 2 step pipeline:
    1. Get all the sets that need to be retrieved.
    2. Determine retrieval methods for each set.

    Returns:
        list[dict]: A list of dictionaries, each containing a retrieval set and its corresponding instruction.
    """
    llm_client = LlmClient.from_config(LlmConfig.from_name("o3_mini"))

    prompt = f"""
    Given the user prompt: {pipeline_execution_request.original_prompt}
    within a document that contains the following text:
    {pipeline_execution_request.text_before_selection}

    <<<USER CURSOR>>>

    {pipeline_execution_request.text_after_selection}

    I need to retrieve information of external sets of information via search, file retrieval, file system examination, or other means.
    Please return a list of sets of information that I need to retrieve, and the instructions for retrieval.
    """

    return llm_client.single_shot(
        prompt=prompt,
        response_type=RetrievalSets,
        message_history=LlmMessageHistory(
            messages=[AgenticContextMessage(), DriverApplicationMessage()]
        ),
    ).parsed_content


if __name__ == "__main__":
    from shared.agents.data_scope import DataScope

    prompts = [
        "How to initialize the adxl355 driver in no-OS/drivers/accel/adxl355/adxl355.c?",
        "Explain the I2C communication configuration for adxl355 in the documentation.",
        "How to set up device channels for adxl355 as described in adxl355.h?",
        "What are the steps for register configuration in adxl355 according to the PDF documentation?",
        "How to configure interrupts for adxl355 in the no-OS driver code?",
        "Describe the process of conducting measurements with adxl355 in the source files.",
        "What are the basic operations with the adxl355 driver as per the API examples?",
        "How to handle errors in adxl355 driver operations as outlined in the documentation?",
        "Explain the IIO support for adxl355 in the no-OS driver.",
        "What additional features does the adxl355 driver offer beyond basic operations, according to the PDF?",
    ]

    for prompt in prompts:
        pipeline_execution_request = PipelineExecutionRequest(
            original_prompt=prompt,
            text_before_selection="This is some text before the cursor.",
            text_after_selection="This is some text after the cursor.",
            selected_text=None,
            datascope=DataScope(),
        )

        retrieval_sets = get_retrieval_instructions(pipeline_execution_request)
        print(f"Prompt: {prompt}")
        print(f"Retrieval Sets: {retrieval_sets}")
        print("\n")
