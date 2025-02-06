from shared.interfaces.agents.data_scope import DataScope
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.clients.llm_generation_response import LlmGenerationResponse
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message import (
    LlmMessage,
)
from shared.v3.messages.llm_message_history import LlmMessageHistory
from shared.v3.messages.llm_message_kind import MessageKind
from shared.v3.tools.agent_tool import (
    LlmTool,
    LlmToolContext,
    LlmToolResponse,
)


class BaseAgent:
    def __init__(
        self,
        datascope: DataScope,
        config: LlmConfig,
        tools: list[LlmTool] | None = None,
        response_type: type | None = None,
    ) -> None:
        self.message_history = LlmMessageHistory(messages=[])
        self.tools = tools if tools is not None else []
        self.client = LlmClient.from_config(config)
        self.datascope = datascope
        self.references = []
        self.response_type = response_type
        self.config = config

    def add_message(
        self,
        message_kind: MessageKind,
        content: str,
        message_id: str | None = None,
        name: str | None = None,
    ) -> None:
        message = LlmMessage(
            message_kind=message_kind, content=content, message_id=message_id, name=name
        )
        self.message_history.add_message(message)

    # def execute_tool(self, tool_name: str, id: str, **kwargs) -> LlmToolResponse:
    #     for tool in self.tools:
    #         print(tool.__class__.__name__)
    #         if tool.__class__.__name__ == tool_name:
    #             tool_context = LlmToolContext(datascope=self.datascope, llm_config=None)
    #             return tool.execute(_tool_context=tool_context, **kwargs)
    #     return LlmToolResponseError(
    #         message_kind=MessageKind.TOOL_CALL,
    #         tool_call_id=id,
    #         error_message=f"Tool {tool_name} not found.",
    #     )

    def invoke(
        self, prompt: str | None = None, iterations: int = 1
    ) -> LlmGenerationResponse:
        self.add_message(MessageKind.USER, prompt)
        for _ in range(iterations):
            print(self.message_history.messages)
            response = self.client.generate(
                prompt=prompt,
                message_history=self.message_history,
                tools=self.tools,
                response_type=self.response_type,
            )
            self.message_history.add_message(
                LlmMessage(
                    message_kind=MessageKind.ASSISTANT,
                    content=None,
                    refusal=None,
                    role="assistant",
                    audio=None,
                    function_call=None,
                    tool_calls=[
                        {
                            "id": tool_call.id,
                            "function": {
                                "arguments": tool_call.parsed_tool.function.parsed_arguments,
                                "name": tool_call.parsed_tool.function.name,
                                "parsed_arguments": tool_call.parsed_tool.function.parsed_arguments,
                            },
                            "type": "function",
                        }
                        for tool_call in response.tool_calls
                    ],
                    parsed=None,
                )
            )

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_response: LlmToolResponse = tool_call.parsed_tool.execute(
                        LlmToolContext(
                            datascope=self.datascope,
                            llm_config=self.config,
                            tool_call_id=tool_call.id,
                        )
                    )
                    self.message_history.add_message(tool_response.to_message())
            else:
                return response
