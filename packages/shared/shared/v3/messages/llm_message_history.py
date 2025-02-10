from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call_param import (
    Function as OpenAIFunction,
)
from pydantic import BaseModel
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.messages.llm_message_kind import MessageKind


class LlmMessageHistory(BaseModel):
    messages: list[LlmMessage]

    def add_message(self, message: LlmMessage) -> None:
        self.messages.append(message)

    def to_openai_messagelist_gpt(self) -> list[ChatCompletionMessageParam]:
        """
        Converts the message history to a format suitable for OpenAI's strict API,
        including tool call messages with tool_call_id.

        :return: A list of messages formatted for the OpenAI strict API.
        """
        messages: list[ChatCompletionMessageParam] = []
        for message in self.messages:
            if message.message_kind == MessageKind.TOOL_CALL_RESPONSE:
                message_dict: ChatCompletionToolMessageParam = (
                    ChatCompletionToolMessageParam(
                        role="tool",
                        content=message.content,
                        tool_call_id=message.tool_response.id,
                    )
                )
            elif message.message_kind == MessageKind.ASSISTANT:
                message_dict: ChatCompletionAssistantMessageParam = (
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=message.content,
                        tool_calls=message.tool_requests,
                    )
                )
            elif message.message_kind == MessageKind.DEVELOPER:
                message_dict: ChatCompletionDeveloperMessageParam = (
                    ChatCompletionDeveloperMessageParam(
                        role="developer",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.TOOL_CALL_REQUEST:
                message_dict: ChatCompletionToolMessageParam = (
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=message.content,
                        tool_calls=[
                            ChatCompletionMessageToolCallParam(
                                id=tool_request.id,
                                function=OpenAIFunction(
                                    name=tool_request.name,
                                    arguments=tool_request.arguments,
                                ),
                                type="function",
                            )
                            for tool_request in message.tool_requests
                        ],
                    )
                )
            elif message.message_kind == MessageKind.SYSTEM:
                message_dict: ChatCompletionSystemMessageParam = (
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.USER:
                message_dict: ChatCompletionUserMessageParam = (
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.ITERATION and not any(
                m.message_kind == MessageKind.ITERATION
                for m in self.messages[self.messages.index(message) + 1 :]
            ):
                message_dict = ChatCompletionUserMessageParam(
                    role="user",
                    content=message.content,
                )
            messages.append(message_dict)

        return messages

    def to_openai_messagelist_o_series(self) -> list:
        messages = []
        for message in self.messages:
            if message.message_kind == MessageKind.TOOL_CALL_RESPONSE:
                message_dict: ChatCompletionDeveloperMessageParam = (
                    ChatCompletionDeveloperMessageParam(
                        role="user",
                        content=message.content,
                    )
                )
            if message.message_kind == MessageKind.SYSTEM:
                message_dict: ChatCompletionDeveloperMessageParam = (
                    ChatCompletionDeveloperMessageParam(
                        role="developer",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.ASSISTANT:
                message_dict: ChatCompletionAssistantMessageParam = (
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=message.content,
                        tool_calls=message.tool_requests,
                    )
                )
            elif message.message_kind == MessageKind.DEVELOPER:
                message_dict: ChatCompletionDeveloperMessageParam = (
                    ChatCompletionDeveloperMessageParam(
                        role="developer",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.TOOL_CALL_REQUEST:
                message_dict: ChatCompletionToolMessageParam = (
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=message.content
                    )
                )
            elif message.message_kind == MessageKind.USER:
                message_dict: ChatCompletionUserMessageParam = (
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.ITERATION and not any(
                m.message_kind == MessageKind.ITERATION
                for m in self.messages[self.messages.index(message) + 1 :]
            ):
                message_dict = ChatCompletionUserMessageParam(
                    role="user",
                    content=message.content,
                )
            messages.append(message_dict)

        return messages

    def to_openai_messagelist_user_type(self) -> list:
        messages = []
        for message in self.messages:
            if message.message_kind == MessageKind.TOOL_CALL_RESPONSE:
                message_dict: ChatCompletionUserMessageParam = (
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                )
            if message.message_kind == MessageKind.SYSTEM:
                message_dict: ChatCompletionUserMessageParam = (
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.ASSISTANT:
                message_dict: ChatCompletionAssistantMessageParam = (
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=message.content,
                        tool_calls=message.tool_requests,
                    )
                )
            elif message.message_kind == MessageKind.DEVELOPER:
                message_dict: ChatCompletionUserMessageParam = (
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.TOOL_CALL_REQUEST:
                message_dict: ChatCompletionToolMessageParam = (
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=message.content
                    )
                )
            elif message.message_kind == MessageKind.USER:
                message_dict: ChatCompletionUserMessageParam = (
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                )
            elif message.message_kind == MessageKind.ITERATION and not any(
                m.message_kind == MessageKind.ITERATION
                for m in self.messages[self.messages.index(message) + 1 :]
            ):
                message_dict = ChatCompletionUserMessageParam(
                    role="user",
                    content=message.content,
                )
            messages.append(message_dict)

        return messages
