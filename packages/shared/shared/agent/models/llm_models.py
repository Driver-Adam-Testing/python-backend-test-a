import os
from enum import Enum

import toml
from pydantic import BaseModel


class SupportedModel(BaseModel):
    model_id: str
    provider: str
    context_window_size: int
    max_output_tokens: int


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ModelConfig:
    SUPPORTED_MODELS = []

    @classmethod
    def load_models(cls):
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "llm_model_config.toml"
        )
        config = toml.load(config_path)
        for _, model_details in config["models"].items():
            cls.SUPPORTED_MODELS.append(
                SupportedModel(
                    model_id=model_details["model_id"],
                    provider=model_details["provider"],
                    context_window_size=model_details["context_window_size"],
                    max_output_tokens=model_details["max_output_tokens"],
                )
            )

    @classmethod
    def get_default_model(cls):
        default_model_name = toml.load(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "llm_model_config.toml"
            )
        )["model_config"]["default_model"]
        return next(
            (
                model
                for model in cls.SUPPORTED_MODELS
                if model.model_id == default_model_name
            ),
            None,
        )

    @classmethod
    def get_model_by_provider(cls, provider: ModelProvider):
        return [model for model in cls.SUPPORTED_MODELS if model.provider == provider]

    @classmethod
    def get_model_config_by_model(cls, model_name: str) -> SupportedModel | None:
        return next(
            (model for model in cls.SUPPORTED_MODELS if model.model_id == model_name),
            None,
        )


ModelConfig.load_models()
