from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel
from shared import prompts
from shared.agent.agent_openai_strict import OpenAIStrictAgent
from shared.agent.models.llm_models import ModelConfig
from shared.agent.tools.open_file_tool import OpenFileTool
from shared.agent.tools.search_tool import SearchTool
from shared.interfaces.agents.pipeline_configuration import (
    PipelineStepConfiguration,
    PipelineStepResponse,
)
from shared.interfaces.agents.prompt import PromptWithContext


class CodeSnippets(BaseModel):
    """
    A model representing a collection of code snippets.

    Attributes:
        snippets (list[str]): A list of code snippets.
    """

    snippets: list[str]


class CodeVerification(BaseModel):
    """
    A model representing the verification details of a code snippet.

    Attributes:
        supporting_evidence_paths (list[str]): A list of paths supporting the verification.
        input_code (str): The original code snippet.
        corrected_code (str | None): The corrected code snippet, if any.
        corrected (bool): A flag indicating whether the code snippet was corrected.
        rationale (str): The rationale for correcting the code snippet.
    """

    supporting_evidence_paths: list[str]
    input_code: str
    corrected_code: str | None
    corrected: bool
    rationale: str


def run_agent_find_code_snippets(input: PipelineStepConfiguration):
    agent = OpenAIStrictAgent(
        model=ModelConfig.default().model_id,
        paths=input.scope.paths,
        organization_id=input.scope.organization_id,
        response_format=CodeSnippets,
    )
    agent.add_message(prompts.voice.software_engineer.MESSAGE)
    agent.add_message(prompts.task.code_snippet_extractor.MESSAGE)

    snippets = agent.invoke(str(input.prompt))
    return PipelineStepResponse(
        agent_id=agent.agent_id, agent_result=snippets, search_results=[]
    )


def run_agent_code_critic_verification(input: PipelineStepConfiguration):
    agent = OpenAIStrictAgent(
        model=ModelConfig.default().model_id,
        paths=input.scope.paths,
        organization_id=input.scope.organization_id,
        max_iterations=3,
        tools=[SearchTool, OpenFileTool],
        response_format=CodeVerification,
    )
    agent.add_message(prompts.task.code_critic_verifier.MESSAGE)

    response: CodeVerification = agent.invoke(str(input.prompt))

    return PipelineStepResponse(
        agent_id=agent.agent_id,
        agent_result=response,
        search_results=agent.search_results,
    )


def run_agent_code_critic__extract_verify_correct(input: PipelineStepConfiguration):
    original_document = input.prompt.prompt
    snippets = run_agent_find_code_snippets(input)
    verification_results = []

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                run_agent_code_critic_verification,
                PipelineStepConfiguration(
                    prompt=PromptWithContext(prompt=snippet), scope=input.scope
                ),
            )
            for snippet in snippets.agent_result.snippets
        ]

        for future in as_completed(futures):
            verification_results.append(future.result())
    corrected_document = original_document
    for verification_result in verification_results:
        if verification_result.agent_result.corrected:
            corrected_document = corrected_document.replace(
                verification_result.agent_result.input_code,
                verification_result.agent_result.corrected_code,
            )
    final_results = [snippets]
    final_results.extend(verification_results)
    final_results.append(
        PipelineStepResponse(
            agent_id=None, agent_result=corrected_document, search_results=[]
        )
    )
    return PipelineStepResponse(
        agent_id=None, agent_result=final_results, search_results=[]
    )
