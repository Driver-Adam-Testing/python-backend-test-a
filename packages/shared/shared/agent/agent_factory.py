from shared.agent.agent_anthropic_strict import AnthropicStrictAgent
from shared.agent.agent_openai_strict import OpenAIStrictAgent
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
        return OpenAIStrictAgent(
            model=model.model_id,
            max_iterations=max_iterations,
            tools=tools,
            organization_id=organization_id,
            paths=paths,
        )
    elif model.provider == ModelProvider.ANTHROPIC:
        return AnthropicStrictAgent(
            model=model.model_id,
            max_iterations=max_iterations,
            tools=tools,
            organization_id=organization_id,
            paths=paths,
        )
    else:
        raise ValueError(f"Provider {model.provider} is not supported.")
