from pydantic import BaseModel
from shared.interfaces.agents.data_scope import DataScope
from shared.v3.agents.agent import BaseAgent
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.tools.hybrid_search import HybridSearchTool


class ListResponse(BaseModel):
    list_of_responses: list[str]


default_config = LlmConfig.default()


def print_default_llm_config():
    """
    Prints the default LLM configuration.
    """
    print("Default LLM Configuration:")
    print(f"Model Name: {default_config.model_name}")
    print(f"Model ID: {default_config.model_id}")
    print(f"Provider: {default_config.provider}")
    print(f"Max Context Window: {default_config.max_context_window}")
    print(f"Optimal Context Window: {default_config.optimal_context_window}")
    print(f"Max Output Tokens: {default_config.max_output_tokens}")
    print(f"API Kind: {default_config.api_kind}")


def test_generate_with_prompt():
    """
    Loads the default configuration into a client and runs generate with a test prompt.
    """
    client = LlmClient.from_config(default_config)
    test_prompt = "List the presidents of the United States in the 20th century."
    response = client.generate(prompt=test_prompt, response_type=ListResponse)
    print("Generated Response:")
    print(response)


def test_agent_invoke():
    """
    Creates an agent and asks it for information about a codebase.
    """
    datascope = DataScope(
        node_ids=["158beef1-301c-4b98-aa8e-d90fb0cae78f"],
        organization_id="org_xaVHrX52BW5RfZQS",
        user_id="user1",
    )
    agent = BaseAgent(
        datascope=datascope, config=default_config, tools=[HybridSearchTool]
    )
    codebase_prompt = "Describe the architecture of a the included Python web application. Use the Hybrid Search Tool"
    agent_response = agent.invoke(prompt=codebase_prompt, iterations=2)
    print("Agent Response:")
    print(agent_response)


if __name__ == "__main__":
    print_default_llm_config()
    # test_generate_with_prompt()
    test_agent_invoke()
