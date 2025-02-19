import enum

from pydantic import BaseModel
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.pipelines.interfaces.pipeline_request import PipelineExecutionRequest
from shared.v3.static.messages.global_driver_application_messages import (
    AgenticContextMessage,
    DriverApplicationMessage,
)
from shared.v3.utils.parseable import LlmParseable


class PromptInterpretation(LlmParseable):
    """
    Attributes:
        subjects (list[str]): The main topics of the prompt, representing the concepts or entities the user is inquiring about.
        logical_steps (list[PromptSteps]): The steps required to either retrieve information or perform tasks to achieve the user's goal.

    Details:
        - subjects: A list of strings, each representing a subject or topic that the prompt is concerned with.
        - information_sets: A list of strings representing sets of information that must be retrieved from the codebase to achieve the user's goal. If no additional information is needed, this list is empty.
        - logical_steps: A list of strings, each representing a step to either retrieve information or perform a task to achieve the user's goal.

    PromptSteps will usually be used in the following form:
        - step_type: RETRIEVAL, this will be used to retrieve information from or about the codebase. Start with at least one of this step. If all information necessary to achieve the user's goal is already in the prompt, omit this step.
        - step_type: COMPOSITION, this will be used to compose responses. These will be the last steps.

        Attributes:
            step_type (PromptSteps.StepType): The type of step, indicating whether it involves retrieval, composition, or synthesis.
            information_set_to_retrieve (str): The set of information required to complete the step. If no additional information about the codebase or user's goal is needed, this will be an empty string.
            instruction (str): A description of the instruction to be performed.
    """

    class PromptSteps(LlmParseable):
        class StepType(enum.Enum):
            RETRIEVAL = "RETRIEVAL"
            COMPOSITION = "COMPOSITION"

        step_type: StepType
        information_set_to_retrieve: str
        instruction: str

    subjects: list[str]
    logical_steps: list[PromptSteps]


class PromptInterpretationPipelineResponse(BaseModel):
    class PromptInterpretationRetrievalStep(BaseModel):
        information_set_to_retrieve: str
        instruction: str

    class PromptInterpretationCompositionStep(BaseModel):
        instruction: str

    original_prompt: str
    prompt_subjects: list[str]
    retrieval_steps: list[PromptInterpretationRetrievalStep]
    composition_steps: list[PromptInterpretationCompositionStep]


def prompt_interpretation_pipeline(
    pipeline_execution_request: PipelineExecutionRequest,
) -> PromptInterpretationPipelineResponse:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    pi_client = LlmClient.from_config(LlmConfig.from_name("o3_mini"))

    def generate_prompt_interpretation() -> PromptInterpretation:
        return pi_client.generate(
            prompt=pipeline_execution_request.original_prompt,
            response_type=PromptInterpretation,
            message_history=LlmMessageHistory(
                messages=[DriverApplicationMessage(), AgenticContextMessage()]
            ),
        ).parsed_content

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(generate_prompt_interpretation): "prompt_interpretation",
        }

        results = {}
        for future in as_completed(futures):
            task_name = futures[future]
            results[task_name] = future.result()

    prompt_interpretation = results["prompt_interpretation"]

    print(prompt_interpretation)
    return PromptInterpretationPipelineResponse(
        original_prompt=pipeline_execution_request.original_prompt,
        selected_text=pipeline_execution_request.selected_text,
        original_document_text_before_selection=pipeline_execution_request.text_before_selection,
        original_document_text_after_selection=pipeline_execution_request.text_after_selection,
        prompt_subjects=prompt_interpretation.subjects,
        retrieval_steps=[
            PromptInterpretationPipelineResponse.PromptInterpretationRetrievalStep(
                information_set_to_retrieve=step.information_set_to_retrieve,
                instruction=step.instruction,
            )
            for step in prompt_interpretation.logical_steps
            if step.step_type == PromptInterpretation.PromptSteps.StepType.RETRIEVAL
        ],
        composition_steps=[
            PromptInterpretationPipelineResponse.PromptInterpretationCompositionStep(
                instruction=step.instruction,
            )
            for step in prompt_interpretation.logical_steps
            if step.step_type == PromptInterpretation.PromptSteps.StepType.COMPOSITION
        ],
    )
