import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import Self

import httpx
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


MAX_REQUEST_TIMEOUT = 900
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    timeout=httpx.Timeout(
        connect=10.0, write=30.0, read=MAX_REQUEST_TIMEOUT, pool=10.0
    ),
)
if os.environ.get("AZURE_OPENAI_BASE_URL"):
    base_url = os.environ["AZURE_OPENAI_BASE_URL"]
    base_url = f"https://{base_url}/openai/v1/"
    api_key = os.environ["AZURE_OPENAI_KEY_1"]
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=MAX_REQUEST_TIMEOUT,
        http_client=http_client,
    )
else:
    client = AsyncOpenAI(timeout=MAX_REQUEST_TIMEOUT, http_client=http_client)


@dataclass
class ChatOpenAI:
    model: str
    temperature: int
    request_timeout: int
    # client: AsyncOpenAI = field(init=False)

    def __post_init__(self) -> None:
        pass

    @staticmethod
    def get_token_limit(model: str) -> int:
        TOKEN_LIMITS = {
            "gpt-4.1": 1_000_000,
            "o3-mini": 200_000,
            "gpt-4o": 128_000,
            "gpt-5": 272_000,
        }
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
            openai.PermissionDeniedError,
            ValidationError,
        ),
    )
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        output_cfg: OutputConfig = OutputConfig.default(),
    ) -> str:
        # TODO: relax when `gpt-4o` or similar defaults support JSON strict mode.
        if output_cfg.kind == OutputConfigKind.JSON_STRICT and self.model not in [
            "gpt-4o-2024-08-06",
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1",
            "gpt-5",
        ]:
            raise ValueError(f"Model ({self.model}) does not support JSON strict mode")
        if output_cfg.kind == OutputConfigKind.JSON_STRICT:
            if "gpt-5" in self.model:
                response = await client.beta.chat.completions.parse(
                    model=self.model,
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
                response = await client.beta.chat.completions.parse(
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

        elif "o1" in self.model:
            if "o1-mini" in self.model:
                response = await client.chat.completions.create(
                    model=self.model,
                    response_format=output_cfg.into_openai_response_format(),
                    messages=[
                        {
                            "role": "user",
                            "content": user_prompt,
                        },
                    ],
                )
            else:
                response = await client.chat.completions.create(
                    model=self.model,
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
        elif "o3" in self.model or "gpt-5" in self.model:
            response = await client.chat.completions.create(
                model=self.model,
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
            response = await client.chat.completions.create(
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
