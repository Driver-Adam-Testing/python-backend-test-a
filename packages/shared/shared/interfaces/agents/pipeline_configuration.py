import enum
import uuid

from pydantic import BaseModel
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
    step_type: PipelineStepType


class PipelineMode(str, enum.Enum):
    FANOUT = "fan_out"
    SEQUENTIAL = "sequential"


class PipelineSequenceInput(PromptWithContext):
    """
    Input for executing an agent.

    Attributes:
        agent_config (AgentConfiguration): The configuration for the agent.
        scope (AgentScope): The scope of the agent's operation.
    """

    steps: list[PipelineStepConfiguration] | None = None
    scope: DataScope = DataScope(paths=[], organization_id=None)

    def __init__(self, **data):
        super().__init__(**data)
        if self.steps is None:
            self.steps = [PipelineStepConfiguration(step_type=PipelineStepType.DEFAULT)]


class PipelineStepResponse(BaseModel):
    """
    Response from executing an agent.

    Attributes:
        result (str): The result of the agent's execution.
        agent_results (list[AgentResult]): List of agent results.
    """

    agent_id: str | uuid.UUID | None
    agent_result: str | object
    search_results: list[SearchResults] = []


class PipelineResponse(BaseModel):
    step_responses: list[PipelineStepResponse]
