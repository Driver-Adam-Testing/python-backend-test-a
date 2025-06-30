from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Self

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
from shared.utils.decorators import async_retry_with_exponential_backoff


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
    temperature: float
    request_timeout: int
    client: AsyncOpenAI = field(init=False)

    def __post_init__(self) -> None:
        self.client = AsyncOpenAI(timeout=self.request_timeout)

    @staticmethod
    def get_token_limit(model: str) -> int:
        TOKEN_LIMITS = {"gpt-4.1": 1_000_000}
        return TOKEN_LIMITS[model]

    @async_retry_with_exponential_backoff(
        initial_delay=10.0,
        exponential_base=1.0005,
        errors=(
            openai.APITimeoutError,
            openai.RateLimitError,
            openai.InternalServerError,
            openai.APIConnectionError,
            openai.BadRequestError,
            ValidationError,
        ),
    )
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        output_cfg: OutputConfig = OutputConfig.default(),
    ) -> str:
        if output_cfg.kind == OutputConfigKind.JSON_STRICT and self.model != "gpt-4.1":
            raise ValueError(f"Model ({self.model}) does not support JSON strict mode")
        if output_cfg.kind == OutputConfigKind.JSON_STRICT:
            response = await self.client.beta.chat.completions.parse(
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
            response = await self.client.chat.completions.create(
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
