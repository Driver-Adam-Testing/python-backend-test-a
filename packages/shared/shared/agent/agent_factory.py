from shared.agent.agent import AnthropicAgent, OpenAIAgent
from shared.agent.models.llm_models import ModelConfig, ModelProvider


def create_agent(
    workspace_id: str,
    codebase_id: str = None,
    model: str | None = None,
    max_iterations: int = 1,
    tools=None,
):
    if model is None:
        model = ModelConfig.get_default_model()
    else:
        model = ModelConfig.get_model_config_by_model(model)

    if model is None:
        raise ValueError("Model is not supported.")

    if model.provider == ModelProvider.OPENAI:
        return OpenAIAgent(
            workspace_id, codebase_id, model.model_id, max_iterations, tools
        )
    elif model.provider == ModelProvider.ANTHROPIC:
        return AnthropicAgent(
            workspace_id, codebase_id, model.model_id, max_iterations, tools
        )
    else:
        raise ValueError(f"Provider {model.provider} is not supported.")


def get_agent(self, agent_instance_id: str):
    (
        agent_instance,
        agent_messages,
        agent_errors,
        chunk_texts,
    ) = self.collection.get_agent_instance(agent_instance_id)
    if agent_instance is None:
        return None
    agent = OpenAIAgent(
        workspace_id=agent_instance.workspace_id,
        codebase_id=agent_instance.codebase_id,
        model=agent_instance.model,
        id=agent_instance.id,
    )
    for message in agent_messages:
        agent.add_message(message)
    return agent
