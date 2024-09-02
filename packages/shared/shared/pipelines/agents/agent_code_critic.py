from pydantic import BaseModel
from shared.agent.agent_openai_strict import OpenAIStrictAgent
from shared.agent.models.llm_models import ModelConfig
from shared.agent.tools.open_file_tool import OpenFileTool
from shared.agent.tools.search_tool import SearchTool
from shared.interfaces.agents.execute import AgentConfiguration, AgentResult, AgentScope


class CodeSnippets(BaseModel):
    snippets: list[str]


class CodeVerification(BaseModel):
    supporting_paths: list[str]
    original_code_snippet: str
    fixed_code_snippet: str | None
    fixed: bool
    rationale_for_fixing: str


def run_agent_code_critic(
    prompt: str, agent_config: AgentConfiguration, scope: AgentScope
):
    agent = OpenAIStrictAgent(
        model=ModelConfig.get_default_model().model_id,
        paths=scope.paths,
        organization_id=scope.organization_id,
        response_format=CodeSnippets,
    )

    agent.add_message(
        {
            "role": "system",
            "content": """
            You are a system that identifies code snippets in a document and extracts them.
        """,
        }
    )
    agent.add_message(
        {
            "role": "user",
            "content": f"Extract all code snippets in this document. <document>{prompt}</document>",
        }
    )

    snippets = agent.invoke(prompt)
    verifications = []
    for snippet in snippets.snippets:
        verification_agent = OpenAIStrictAgent(
            model=ModelConfig.get_default_model().model_id,
            paths=scope.paths,
            organization_id=scope.organization_id,
            max_iterations=4,
            tools=[SearchTool, OpenFileTool],
            response_format=CodeVerification,
        )
        verification_response = verification_agent.invoke(
            f"""For the code snippet:
                                             <code_snippet>{snippet}</code_snippet>
                                             search for all source code that would be necessary to verify that the code is correct to be used within the context of the source code you're searching. find misspellings, hallucinations, functions, and symbols that don't exist or operate as expected or have other discrepencies between the example and the source.
                                             Depending on search results if the code is incorrect, respond with a fixed code snippet. then  either respond with supporting paths that prove the code example was correct, or prove that the fixed code is correct. If a code snippet gets fixed, return the rationale for fixing it. Respond with whether or not the original snippet was altered, and supporting paths that prove that the source code will execute correctly."""
        )
        verifications.append(verification_response)
    return AgentResult(result=str(verifications), search_results=agent.search_results)
