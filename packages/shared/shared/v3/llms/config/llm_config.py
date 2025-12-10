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
    CLAUDE = "claude"


class SupportedModels(str, Enum):
    """
    Supported models for the LLM config.
    These should always be the same as the names in the TOML file.
    """

    DEFAULT = "default"
    GPT_4O = "gpt_4o"
    GPT_4O_CHAT = "gpt_4o_chat"
    GPT_4O_MINI = "gpt_4o_mini"
    GPT_4O_MINI_CHAT = "gpt_4o_mini_chat"
    O1 = "o1"
    O1_MINI = "o1_mini"
    O3_MINI = "o3_mini"
    CLAUDE_SONNET_3_5 = "claude_sonnet_3_5"
    CLAUDE_SONNET_3_7 = "claude_sonnet_3_7"
    CLAUDE_HAIKU_3_5 = "claude_haiku_3_5"
    GPT_4_1 = "gpt_4_1"
    GPT_4_1_MINI = "gpt_4_1_mini"
    O4_MINI = "o4_mini"


class LlmConfig(BaseModel):
    """
    Represents configuration for a Large Language Model.
    """

    name: str = Field(
        ..., description="Internal name for the model (e.g. 'default', 'chat_gpt4')"
    )
    llm_model_id: str = Field(
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
    def from_name(cls, name: str = "default") -> "LlmConfig":
        """
        Loads a configuration for a given model name from the TOML file.

        - If the model name is not found, raises a ValueError.
        """

        models_dict = cls.from_file(CONFIG_PATH)

        if name not in models_dict:
            # If a name is not a direct key, optionally loop to find by "model_id" if you prefer
            for name, details in models_dict.items():
                if details.get("llm_model_id") == name:
                    name = name
                    break
            else:
                raise ValueError(
                    f"Model configuration for '{name}' not found in {CONFIG_PATH}."
                )

        details = models_dict[name]
        try:
            return cls(
                name=name,
                llm_model_id=details["llm_model_id"],
                provider=details["provider"],
                max_context_window=details["max_context_window"],
                optimal_context_window=details["optimal_context_window"],
                max_output_tokens=details["max_output_tokens"],
                api_kind=details["api_kind"],
            )
        except KeyError as e:
            raise ValueError(
                f"Missing required field '{e.args[0]}' for model '{name}' in {CONFIG_PATH}."
            ) from e

    @classmethod
    def gpt_4o(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.GPT_4O)

    @classmethod
    def gpt_4o_chat(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.GPT_4O_CHAT)

    @classmethod
    def gpt_4o_mini(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.GPT_4O_MINI)

    @classmethod
    def gpt_4o_mini_chat(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.GPT_4O_MINI_CHAT)

    @classmethod
    def o1(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.O1)

    @classmethod
    def o1_mini(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.O1_MINI)

    @classmethod
    def o3_mini(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.O3_MINI)

    @classmethod
    def claude_sonnet_3_5(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.CLAUDE_SONNET_3_5)

    @classmethod
    def claude_sonnet_3_7(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.CLAUDE_SONNET_3_7)

    @classmethod
    def claude_haiku_3_5(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.CLAUDE_HAIKU_3_5)

    @classmethod
    def gpt_4_1(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.GPT_4_1)

    @classmethod
    def gpt_4_1_mini(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.GPT_4_1_MINI)

    @classmethod
    def o4_mini(cls) -> "LlmConfig":
        return cls.from_name(SupportedModels.O4_MINI)
