from pydantic import BaseModel
from shared.agent.tools.open_file_tool import OpenFileTool
from shared.agent.tools.search_tool import SearchTool
from shared.interfaces.agents.execute import (
    AgentConfiguration,
    AgentExecuteInput,
    AgentExecutionResponse,
    AgentScope,
    AgentType,
)
from shared.pipelines.agents.agent_copy_editor import run_agent_copy_editor
from shared.pipelines.agents.agent_default import run_agent_default
from shared.pipelines.agents.agent_prompt_augmentation import (
    run_agent_prompt_augmentation,
)


class EditDocumentContext(BaseModel):
    """
    Context for smart instruction generation.

    Attributes:
        text_before_selection (str): The text before the selected portion.
        selected_text (str): The text that has been selected.
        text_after_selection (str): The text after the selected portion.
    """

    text_before_selection: str
    selected_text: str
    text_after_selection: str


class AgentEditDocumentExecuteInput(AgentExecuteInput):
    """
    Input model for smart instruction generation.

    Attributes:
        prompt (str): The initial prompt for generating instructions.
        context (SmartInstructionContext): The context surrounding the selected text.
    """

    prompt: str
    context: EditDocumentContext
    scope: AgentScope


INSTRUCTION_PROMPT = "Rewrite the selected text part of document. Respond with replacement or appended text for the selected text, which will be rendered as markdown, according to the user prompt."


def run_agent_edit_document(input: AgentEditDocumentExecuteInput):
    prompt_augmentation_agent_configuration = AgentConfiguration(**input.agent_config)
    prompt_augmentation_agent_configuration.iterations = 1
    prompt_augmentation_prompt = run_agent_prompt_augmentation(
        AgentExecuteInput(
            prompt=input.prompt,
            context=input.context.model_dump(),
            agent_config=prompt_augmentation_agent_configuration,
            scope=input.scope,
        )
    )
    default_agent_result = run_agent_default(
        prompt=prompt_augmentation_prompt.agent_result,
        agent_config=AgentConfiguration(
            system_prompts=[
                "interface.technical_context_interface",
                INSTRUCTION_PROMPT,
            ],
            iterations=3,
            tools=[SearchTool, OpenFileTool],
        ),
        scope=input.scope,
    )
    copy_editor_result = run_agent_copy_editor(
        prompt=default_agent_result,
        agent_config=AgentConfiguration(agent_type=AgentType.COPY_EDITOR, iterations=1),
    )
    return AgentExecutionResponse(
        agent_result=copy_editor_result.agent_result,
        search_results=default_agent_result.search_results,
        agent_id=default_agent_result.id,
    )
