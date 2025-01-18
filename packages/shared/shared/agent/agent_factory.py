from pydantic import BaseModel

from shared.agent.agent_anthropic_strict import AnthropicStrictAgent
from shared.agent.agent_openai_strict import OpenAIStrictAgent
from shared.agent.models.llm_models import ModelConfig, ModelProvider
from shared.interfaces.agents.data_scope import DataScope
from shared.usage.llm_session import LLMUsageSession


def create_agent(
    scope: DataScope,
    model: str | None = None,
    max_iterations: int = 1,
    tools: None | object = None,
    response_type: None | BaseModel = None,
    debug: bool = True,
    log: bool = True,
    llm_usage_session: LLMUsageSession = None,
) -> OpenAIStrictAgent | AnthropicStrictAgent:
    model_config = (
        ModelConfig.default() if model is None else ModelConfig.from_name(model)
    )

    if model_config.provider == ModelProvider.OPENAI:
        return OpenAIStrictAgent(
            model=model_config.model_id,
            max_iterations=max_iterations,
            tools=tools,
            scope=scope,
            response_format=response_type,
            log=log,
            debug=debug,
            llm_usage_session=llm_usage_session,
        )
    elif model_config.provider == ModelProvider.ANTHROPIC:
        return AnthropicStrictAgent(
            model=model_config.model_id,
            max_iterations=max_iterations,
            tools=tools,
            scope=scope,
            log=log,
            debug=debug,
        )
    else:
        raise ValueError(f"Provider {model.provider} is not supported.")
