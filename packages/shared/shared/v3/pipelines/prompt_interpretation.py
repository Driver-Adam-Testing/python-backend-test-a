import enum

from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.messages.llm_message_history import LlmMessageHistory
from shared.v3.static.messages.driver_application_messages import (
    AgenticContextMessage,
    DriverApplicationMessage,
)
from shared.v3.utils.parseable import LlmParseable


class PromptClassification(LlmParseable):
    """
    Attributes:
        subjects (list[str]): The main topics of the prompt, representing the concepts or entities the user is inquiring about.
        information_sets (list[str]): The sets of information the user is requesting to consider or retrieve.
        logical_steps (list[str]): The steps required to either retrieve information or perform tasks to achieve the user's goal.

    Details:
        - subjects: A list of strings, each representing a subject or topic that the prompt is concerned with.
        - information_sets: A list of strings representing sets of information that must be retrieved from the codebase to achieve the user's goal. If no additional information is needed, this list is empty.
        - logical_steps: A list of strings, each representing a step to either retrieve information or perform a task to achieve the user's goal.

    PromptSteps will usually be used in the following form:
        - step_type: RETRIEVAL, this will be used to retrieve information from or about the codebase, Start with at least one of this step. If all information necessary to achieve the user's goal is already in the prompt, omit this step.
        - step_type: COMPOSITION, this will be used to compose information from the codebase. They will be the last steps.

        Attributes:
            steps (list[str]): The steps required to either retrieve information or perform tasks to achieve the user's goal.
            step_type (PromptSteps.StepType): The type of step, indicating whether it involves retrieval, composition, or synthesis.
            information_sets_required (list[str]): The sets of information required to complete the step.
            logical_step (str): A description of the logical step to be performed.
    """

    class PromptSteps(LlmParseable):
        class StepType(enum.Enum):
            RETRIEVAL = "RETRIEVAL"
            COMPOSITION = "COMPOSITION"

        step_type: StepType
        information_sets_required: list[str]
        logical_step: str

    subjects: list[str]
    logical_steps: list[PromptSteps]


def prompt_interpretation(prompt: str) -> LlmMessage:
    subject_and_format = LlmClient.from_config(LlmConfig.from_name("o3_mini")).generate(
        prompt=prompt,
        response_type=PromptClassification,
        message_history=LlmMessageHistory(
            messages=[DriverApplicationMessage(), AgenticContextMessage()]
        ),
    )
    print("Prompt:", prompt)
    print("Subjects:", subject_and_format.parsed_content.subjects)
    print("Logical Steps:", subject_and_format.parsed_content.logical_steps)
    print("--------------------------------")
    return subject_and_format


print(PromptClassification.to_instruction_response_string())
prompts = [
    "Generate an architectural diagram that illustrates the major functional blocks of the codebase.",
    "Generate a table that lists each task used in the application.",
    "List the most important APIs that a new developer should become familiar with.",
    "List all files that instantiate a new object of the payment class.",
    "Create a table that shows all interrupts used in the system with a priority of 3 or lower.",
    "Document every function implemented in the file system manager.c relating to battery management.",
    "Generate documentation for the function that calculates the factorial of a number.",
    "Create a technical document explaining the architecture of the user authentication module.",
    "Write documentation for the API endpoints in the payment processing service.",
    "Document the steps to set up the development environment for the project.",
    "Provide a detailed explanation of the data models used in the inventory management system.",
    "Generate a guide on how to deploy the application to a cloud service.",
    "Create a technical document describing the error handling mechanisms in the codebase.",
    "Write documentation for the configuration files used in the project.",
    "Document the process of integrating a third-party library into the project.",
    "Provide a comprehensive guide on the testing framework used in the project.",
    "What are the implications of setting register MX8 to 1?",
    "Give me a way to visualize the database schema of the project.",
    "How do I install this codebase?",
]

for prompt in prompts:
    prompt_interpretation(prompt)
