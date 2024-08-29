import openai
from pydantic import BaseModel
from shared.agent.agent_openai_strict import OpenAIStrictAgent
from shared.agent.models.llm_models import ModelConfig
from shared.agent.tools import agent_tools_strict
from shared.interfaces.agents.execute import AgentConfiguration, AgentResult, AgentScope


class CodeSnippets(BaseModel):
    snippets: list[str]


class CodeVerification(BaseModel):
    supporting_paths: list[str]
    unaltered_code_snippet: str
    altered_code_snippet: str | None
    altered: bool


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
            "content": "Extract all code snippets in this document. <document>{document}</document>",
        }
    )

    snippets = agent.invoke(prompt)
    verifications = []
    for snippet in snippets.snippets:
        verification_agent = OpenAIStrictAgent(
            model=ModelConfig.get_default_model().model_id,
            paths=scope.paths,
            organization_id=scope.organization_id,
            max_iterations=3,
            tools=[openai.pydantic_function_tool(agent_tools_strict.SearchToolInput)],
            response_format=CodeVerification,
        )
        verification_response = verification_agent.invoke(
            f"""For the code snippet:
                                             <code_snippet>{snippet}</code_snippet>
                                             search for all source code that would be necessary to verify that the code is correct to be used within the context of the source code you're searching.
                                             Depending on search results, return either the verified code_snippet, an empty string, or an altered snippet. Respond with whether or not the original snippet was altered, and supporting paths that prove that the source code will execute correctly."""
        )
        verifications.append(verification_response)
    return AgentResult(result=str(verifications), search_results=agent.search_results)
