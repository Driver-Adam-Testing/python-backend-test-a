import logging
import os
from enum import Enum

import toml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "llm_config.toml"
)


class LlmProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ApiKind(str, Enum):
    OPENAI_CHAT_WITH_TOOLS = "openai_chat_with_tools"
    OPENAI_STRICT = "openai_strict"
    OPENAI_O1 = "openai_o1"
    OPENAI_O3 = "openai_o3"


class LlmConfig(BaseModel):
    """
    Represents configuration for a Large Language Model.
    """

    model_name: str = Field(
        ..., description="Internal name for the model (e.g. 'default', 'chat_gpt4')"
    )
    model_id: str = Field(
        ..., description="Provider-specific model identifier (e.g. 'gpt-4')"
    )
    provider: LlmProvider = Field(
        ..., description="Which LLM provider to use (openai, anthropic, google, etc.)"
    )
    max_context_window: int = Field(
        ..., gt=0, description="Max context window size the model supports."
    )
    optimal_context_window: int = Field(
        ..., gt=0, description="Optimal context window size for cost/performance."
    )
    max_output_tokens: int = Field(
        ..., gt=0, description="Max tokens the model can generate in a single response."
    )
    api_kind: ApiKind = Field(
        ..., description="API version to use for the LLM provider."
    )

    @classmethod
    def default(cls) -> "LlmConfig":
        """
        Returns the default LLM configuration,
        which is loaded from the TOML file's 'default' model entry.
        """
        return cls.from_name("default")

    @classmethod
    def from_file(cls, file_path: str | None = None) -> dict[str, dict[str, any]]:
        """
        Safely loads and returns the 'models' dictionary from a TOML file.

        Raises:
          - FileNotFoundError if the TOML file doesn't exist.
          - ValueError if 'models' section doesn't exist or is invalid.
        """
        if file_path is None:
            file_path = CONFIG_PATH

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"TOML configuration file not found: {file_path}")

        try:
            parsed_toml = toml.load(file_path)
        except Exception as e:
            logger.error("Error parsing TOML file: %s", e)
            raise ValueError(f"Error reading TOML file '{file_path}': {e}")

        # Adjust this key to match your actual TOML structure (e.g. "llms" vs. "models")
        key = "llms"
        if key not in parsed_toml or not isinstance(parsed_toml[key], dict):
            raise ValueError(
                f"Missing or invalid '{key}' section in TOML config: {file_path}"
            )

        return parsed_toml[key]

    @classmethod
    def from_name(cls, model_name: str = "default") -> "LlmConfig":
        """
        Loads a configuration for a given model name from the TOML file.

        - If the model name is not found, raises a ValueError.
        """

        models_dict = cls.from_file(CONFIG_PATH)

        if model_name not in models_dict:
            # If a name is not a direct key, optionally loop to find by "model_id" if you prefer
            for name, details in models_dict.items():
                if details.get("model_id") == model_name:
                    model_name = name
                    break
            else:
                raise ValueError(
                    f"Model configuration for '{model_name}' not found in {CONFIG_PATH}."
                )

        details = models_dict[model_name]
        try:
            return cls(
                model_name=model_name,
                model_id=details["model_id"],
                provider=details["provider"],
                max_context_window=details["max_context_window"],
                optimal_context_window=details["optimal_context_window"],
                max_output_tokens=details["max_output_tokens"],
                api_kind=details["api_kind"],
            )
        except KeyError as e:
            raise ValueError(
                f"Missing required field '{e.args[0]}' for model '{model_name}' in {CONFIG_PATH}."
            ) from e
