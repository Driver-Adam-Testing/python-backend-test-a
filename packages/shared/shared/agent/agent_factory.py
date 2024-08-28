from shared.agent.agent_anthropic import AnthropicAgent
from shared.agent.agent_openai import OpenAIAgent
from shared.agent.models.llm_models import ModelConfig, ModelProvider


def create_agent(
    organization_id: str,
    paths: list[str] | None,
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
            model=model.model_id,
            max_iterations=max_iterations,
            tools=tools,
            organization_id=organization_id,
            paths=paths,
        )
    elif model.provider == ModelProvider.ANTHROPIC:
        return AnthropicAgent(
            model=model.model_id,
            max_iterations=max_iterations,
            tools=tools,
            organization_id=organization_id,
            paths=paths,
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
        model=agent_instance.model,
        id=agent_instance.id,
    )
    for message in agent_messages:
        agent.add_message(message)
    return agent
