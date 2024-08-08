from dataclasses import dataclass, field

import openai
from openai import OpenAI

from .decorators import retry_with_exponential_backoff


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
        ),
    )
    def generate_response(
        self, system_prompt: str, user_prompt: str, use_json_mode: bool = False
    ):
        format = "json_object" if use_json_mode else "text"
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": format},
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

    # def generate_response(
    #     self, system_prompt: str, user_prompt: str, response_format: Type[BaseModel] | None = None
    # ):
    #     format = {"type": "text"} if response_format is None else response_format
    #     response = self.client.chat.completions.create(
    #         model=self.model,
    #         temperature=self.temperature,
    #         response_format=format,
    #         messages=[
    #             {
    #                 "role": "system",
    #                 "content": system_prompt,
    #             },
    #             {
    #                 "role": "user",
    #                 "content": user_prompt,
    #             },
    #         ],
    #     )
    #     return response.choices[0].message.content
