import openai
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message_history import LlmMessageHistory
from shared.v3.tools.agent_tool import LlmTool


class OpenAiStrictWithSystemClient(LlmClient):
    def __init__(self, config: LlmConfig) -> None:
        super().__init__(config)
        self.client = openai.OpenAI()

    def generate(
        self,
        prompt: str | None = None,
        response_type: type | None = None,
        message_history: LlmMessageHistory | None = None,
        tools: list[LlmTool] | None = None,
    ) -> any:
        completion_kwargs = {
            "model": self.config.model_id,
            "messages": message_history.to_messagelist_openai_strict()
            if message_history
            else [],
        }
        if prompt:
            completion_kwargs["messages"].append({"role": "user", "content": prompt})

        if tools:
            processed_tools = [openai.pydantic_function_tool(tool) for tool in tools]
            completion_kwargs["tools"] = processed_tools
            completion_kwargs["tool_choice"] = "auto"

        if response_type:
            completion_kwargs["response_format"] = response_type

        try:
            response = self.client.beta.chat.completions.parse(**completion_kwargs)
            return response.choices[0].message
        except Exception as e:
            return f"Error generating response: {e}"
