from shared.agent.agent_anthropic_strict import AnthropicStrictAgent
from shared.agent.agent_openai_strict import OpenAIStrictAgent
from shared.agent.models.llm_models import ModelConfig, ModelProvider


def create_agent(
    organization_id: str,
    paths: list[str] | None,
    model: str | None = None,
    max_iterations: int = 1,
    tools=None,
    response_type=None,
):
    model_config = (
        ModelConfig.default() if model is None else ModelConfig.from_name(model)
    )

    if model_config.provider == ModelProvider.OPENAI:
        return OpenAIStrictAgent(
            model=model_config.model_id,
            max_iterations=max_iterations,
            tools=tools,
            organization_id=organization_id,
            paths=paths,
            response_format=response_type,
        )
    elif model_config.provider == ModelProvider.ANTHROPIC:
        return AnthropicStrictAgent(
            model=model_config.model_id,
            max_iterations=max_iterations,
            tools=tools,
            organization_id=organization_id,
            paths=paths,
        )
    else:
        raise ValueError(f"Provider {model.provider} is not supported.")
