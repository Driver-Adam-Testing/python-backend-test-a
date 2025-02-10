import enum

from shared.interfaces.agents.data_scope import DataScope
from shared.v3.agents.agent import BaseAgent
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.static.response_types.response_type_table import TableResponse
from shared.v3.static.tools.hybrid_search import HybridSearchTool
from shared.v3.utils.parseable import LlmParseable


class StepOne(LlmParseable):
    """
    StepOne is a class that represents the first step in processing a user's request.
    It includes the type of user request and whether the request can be answered with existing context.

    Attributes:
        user_request_type (StepOne.UserRequestType): The type of user request.
            - SET
            - PROSE
            - OTHER
        request_can_be_answered_with_existing_context (bool): Indicates if the request can be answered with existing context.
    """

    class UserRequestType(enum.Enum):
        SET = "SET"
        PROSE = "PROSE"
        OTHER = "OTHER"

    user_request_type: UserRequestType
    request_can_be_answered_with_existing_context: bool


class StepTwo(LlmParseable):
    """The user has provided a request for information that may require external context in order to be answered.
    The application will use tools to search and traverse a codebase in order to find the external context necessary to generate the table.
    In the future, it will provide that external context to a tool to synthesize the answer.
    The first step is to analyze the user's request and determine the most relevant steps to retrieve external context.

    Attributes:
        user_request_type (StepTwo.UserRequestType): The type of user request.
        request_requires_external_context (bool): Indicates if the request requires external context.
        request_requires_traversal_of_the_codebase_filesystem (bool): Indicates if the request requires traversal of the codebase filesystem.
        user_requests_a_set (bool): Indicates if the user requests a set.
        user_requests_a_complete_set (bool): Indicates if the user requests a complete set.
        specific_files_or_directories_mentioned (list[str] | None): Specific files or directories mentioned in the request.
        specific_explicit_attributes_mentioned (list[str] | None): Specific explicit attributes mentioned in the request.
        specific_conceptual_attributes_mentioned (list[str] | None): Specific conceptual attributes mentioned in the request.

    UserRequestTypes:
        - CONCEPTUAL_SEMANTIC_SET: Requests involving conceptual or semantic groupings of items.
        - ANALYTICAL_SET: Requests for sets of defined items that meet specific analytical criteria.
        - REAL_DEFINED_SET: Requests where the user has defined specific criteria, and the application retrieves and enumerates them.
        - ABSTRACT_SET: Requests involving abstract groupings or categories.
        - GENERAL_PROSE: Requests for general narrative or descriptive text.
        - SUMMARIZATION: Requests to summarize existing information.
        - FORMATTING: Requests to format existing context.
        - OTHER: Any other type of request not covered by the above categories.
    """

    class UserRequestType(enum.Enum):
        CONCEPTUAL_SEMANTIC_SET = "CONCEPTUAL_SEMANTIC_SET"
        ANALYTICAL_SET = "ANALYTICAL_SET"
        REAL_DEFINED_SET = "REAL_DEFINED_SET"
        ABSTRACT_SET = "ABSTRACT_SET"
        GENERAL_PROSE = "GENERAL_PROSE"
        SUMMARIZATION = "SUMMARIZATION"
        FORMATTING = "FORMATTING"
        OTHER = "OTHER"

    user_request_type: UserRequestType
    request_requires_external_context: bool
    request_requires_traversal_of_the_codebase_filesystem: bool
    user_requests_a_set: bool
    user_requests_a_complete_set: bool
    specific_files_or_directories_mentioned: list[str]
    specific_explicit_attributes_mentioned: list[str]
    specific_conceptual_attributes_mentioned: list[str]

    def to_markdown(self) -> str:
        """
        Convert the StepTwo instance to a markdown string representation.

        Returns:
            str: The markdown string representation of the StepTwo instance.
        """
        return f"**User Request Type:** {self.user_request_type.value}\n"


print(StepOne.to_instruction_response_string())
print(StepTwo.to_instruction_response_string())


def smart_instruction_table(prompt: str, datascope: DataScope) -> TableResponse:
    print("\033[94m" + "=" * 50)
    print(f"Prompt: {prompt}")
    config = LlmConfig.from_name("gpt_4o_mini")
    client = LlmClient.from_config(config)

    step_one_response = client.generate(prompt=prompt, response_type=StepOne)

    print(step_one_response.parsed_content)
    if step_one_response.parsed_content.request_can_be_answered_with_existing_context:
        print("Request can be answered with existing context")
    else:
        print("Request cannot be answered with existing context")
    step_two_response = client.generate(prompt=prompt, response_type=StepTwo)
    print("\033[94m" + "=" * 50)
    print(f"Prompt: {prompt}")
    print(step_two_response.parsed_content)
    config = LlmConfig.default()
    agent = BaseAgent(
        datascope=datascope,
        config=config,
        tools=[HybridSearchTool],
        response_type=TableResponse,
    )

    response = agent.invoke(prompt=prompt, iterations=5, debug=True)

    if isinstance(response, TableResponse):
        return response
    else:
        raise ValueError("The response is not of type TableResponse")
