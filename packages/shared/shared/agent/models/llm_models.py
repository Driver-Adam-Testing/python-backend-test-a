import os
from enum import Enum

import toml
from pydantic import BaseModel


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class SystemPromptConfig(str, Enum):
    NONE = "none"
    ONE = "one"
    MANY = "many"


class ModelConfig(BaseModel):
    model_name: str
    model_id: str
    provider: str
    context_window_size: int
    max_output_tokens: int
    system_prompts: str

    @classmethod
    def default(cls) -> "ModelConfig":
        return cls.from_name("default")

    @classmethod
    def from_name(cls, model_name: str = "default") -> "ModelConfig":
        model_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "llm_model_config.toml"
        )
        model_config = toml.load(model_config_path)
        for name, details in model_config["models"].items():
            if details["model_id"] == model_name or name == model_name:
                return cls(
                    model_name=name,
                    model_id=details["model_id"],
                    provider=details["provider"],
                    context_window_size=details["context_window_size"],
                    max_output_tokens=details["max_output_tokens"],
                    system_prompts=details["system_prompts"],
                )
        raise ValueError(f"Model configuration for '{model_name}' not found.")
