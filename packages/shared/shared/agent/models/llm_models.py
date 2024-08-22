import os
from enum import Enum

import toml
from pydantic import BaseModel


class SupportedModel(BaseModel):
    model_name: str
    model_id: str
    provider: str
    context_window_size: int
    max_output_tokens: int


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


model_config_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "llm_model_config.toml"
)
SUPPORTED_MODELS = []
model_config = toml.load(model_config_path)
for model_name, model_details in model_config["models"].items():
    SUPPORTED_MODELS.append(
        SupportedModel(
            model_name=model_name,
            model_id=model_details["model_id"],
            provider=model_details["provider"],
            context_window_size=model_details["context_window_size"],
            max_output_tokens=model_details["max_output_tokens"],
        )
    )


class ModelConfig:
    @classmethod
    def get_default_model(cls):
        return cls.get_model_config_by_model("default")

    @classmethod
    def get_model_config_by_model(cls, model_name: str) -> SupportedModel | None:
        return next(
            (
                model
                for model in SUPPORTED_MODELS
                if model.model_id == model_name or model.model_name == model_name
            ),
            None,
        )
