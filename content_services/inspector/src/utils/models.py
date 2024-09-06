from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Self

import openai
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from shared.utils.decorators import retry_with_exponential_backoff


class OutputConfigKind(Enum):
    JSON_MODE = auto()
    JSON_STRICT = auto()
    TEXT = auto()


class OutputConfig(BaseModel):
    kind: OutputConfigKind
    payload: type[BaseModel] | None = None

    @classmethod
    def default(cls) -> Self:
        return cls(kind=OutputConfigKind.TEXT)

    def into_openai_response_format(self) -> dict[str, str] | type[BaseModel]:
        match self.kind:
            case OutputConfigKind.JSON_MODE:
                return {"type": "json_object"}
            case OutputConfigKind.JSON_STRICT:
                return self.payload
            case OutputConfigKind.TEXT:
                return {"type": "text"}
            case _:
                raise ValueError("Unreachable")


@dataclass
class ChatOpenAI:
    model: str
    temperature: int
    request_timeout: int
    client: OpenAI = field(init=False)

    def __post_init__(self):
        self.client = OpenAI(timeout=self.request_timeout)

    @retry_with_exponential_backoff(
        initial_delay=10.0,
        exponential_base=1.0005,
        errors=(
            openai.APITimeoutError,
            openai.RateLimitError,
            openai.InternalServerError,
            openai.APIConnectionError,
            openai.NotFoundError,
            ValidationError,
        ),
    )
    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        output_cfg: OutputConfig = OutputConfig.default(),
    ):
        # TODO: relax when `gpt-4o` or similar defaults support JSON strict mode.
        if (
            output_cfg.kind == OutputConfigKind.JSON_STRICT
            and not self.model == "gpt-4o-2024-08-06"
        ):
            raise ValueError(f"Model ({self.model}) does not support JSON strict mode")
        if output_cfg.kind == OutputConfigKind.JSON_STRICT:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                temperature=self.temperature,
                response_format=output_cfg.into_openai_response_format(),
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format=output_cfg.into_openai_response_format(),
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )
        return response.choices[0].message.content
