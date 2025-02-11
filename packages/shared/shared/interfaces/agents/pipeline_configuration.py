import enum
import uuid

from pydantic import BaseModel, Field
from shared.interfaces.agents.agent_configuration import AgentConfiguration
from shared.interfaces.agents.data_scope import DataScope
from shared.interfaces.agents.prompt import PromptWithContext
from shared.interfaces.search import SearchResults


class PipelineStepType(str, enum.Enum):
    """
    Enum representing different types of agents.
    """

    DEFAULT = "default"
    PROMPT_AUGMENTATION = "prompt_augmentation"
    COPY_EDITOR = "copy_editor"
    CODE_CRITIC = "code_critic"
    SMART_INSTRUCTION = "smart_instruction"
    EDIT_DOCUMENT = "edit_document"


class PipelineStepConfiguration(AgentConfiguration):
    prompt: PromptWithContext | None = None
    step_type: PipelineStepType = PipelineStepType.DEFAULT

    def into_pipeline_step(
        self,
        sequence_prompt: PromptWithContext | None,
        input_scope: DataScope | None,
        working_response: str | None,
    ) -> "PipelineStepConfiguration":
        new_step = self.model_copy()
        new_step.prompt = sequence_prompt or self.prompt
        new_step.scope = input_scope or self.scope

        if new_step.step_type == PipelineStepType.SMART_INSTRUCTION:
            new_step.tool_names = [
                "SearchTool",
                "OpenFileTool",
                "CodebaseFolderSummaryTool",
            ]
            new_step.system_prompts = [
                "voice.software_engineer",
                "interface.technical_context_interface",
                "task.selected_text",
            ]
            new_step.iterations = 3

        if new_step.step_type == PipelineStepType.EDIT_DOCUMENT:
            new_step.tool_names = ["SearchTool", "OpenFileTool"]
            new_step.system_prompts = [
                "voice.software_engineer",
                "voice.copy_editor",
                "interface.technical_context_interface",
                "task.selected_text",
                "task.edit_document",
            ]
            new_step.iterations = 2

        if working_response:
            if new_step.step_type in [
                PipelineStepType.CODE_CRITIC,
                PipelineStepType.COPY_EDITOR,
            ]:
                new_step.prompt.prompt = working_response
            elif new_step.step_type == PipelineStepType.DEFAULT:
                instructions = sequence_prompt.prompt if sequence_prompt else ""
                new_step.prompt.prompt = (
                    f"Enhance the working document:\n<document>\n{working_response}\n</document>\n"
                    f"According to the instructions\n{instructions}"
                )

        return new_step


class PipelineMode(str, enum.Enum):
    FANOUT = "fan_out"
    SEQUENTIAL = "sequential"


class PipelineInput(PromptWithContext):
    """
    Input for executing an agent.

    Attributes:
        agent_config (AgentConfiguration): The configuration for the agent.
        scope (AgentScope): The scope of the agent's operation.
    """

    steps: list[PipelineStepConfiguration] = Field(
        default_factory=lambda: [
            PipelineStepConfiguration(step_type=PipelineStepType.DEFAULT)
        ]
    )
    # TODO: Make this Non-nullable?
    scope: DataScope | None = None
    response_format: type


class PipelineStepResponse(BaseModel):
    """
    Response from executing a pipeline step.

    Attributes:
        agent_id (str | uuid.UUID | None): The ID of the agent that executed the step.
        agent_result (str | object): The result produced by the agent.
        search_results (list[SearchResults]): List of search results related to the step.
    """

    agent_id: str | uuid.UUID | None
    agent_result: str | object
    search_results: list[SearchResults] = []


class PipelineResponse(BaseModel):
    step_responses: list[PipelineStepResponse]
    final_result: str
