from pydantic import BaseModel
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.messages.llm_message_kind import MessageKind


class LlmMessageHistory(BaseModel):
    messages: list[LlmMessage]

    def add_message(self, message: LlmMessage) -> None:
        self.messages.append(message)

    def get_messages(self) -> list[LlmMessage]:
        return self.messages

    def to_messagelist_openai_strict(self) -> list[dict]:
        """
        Converts the message history to a format suitable for OpenAI's strict API,
        including tool call messages with tool_call_id.

        :return: A list of messages formatted for the OpenAI strict API.
        """
        # Prepare the messages for the API call
        messages = []
        for message in self.messages:
            try:
                message_dict = {
                    "role": message.message_kind,
                    "content": message.content,
                }
                if message.message_kind == MessageKind.TOOL_CALL:
                    message_dict["tool_call_id"] = message.message_id
                messages.append(message_dict)
            except Exception as e:
                print(message)
                raise e
        return messages

    def to_anthropic_chat_user_messages(self) -> list[dict]:
        """
        Returns all messages except those with the 'system' role.

        :return: A list of messages excluding system messages.
        """
        return [
            {"role": message.message_kind.value, "content": message.content}
            for message in self.messages
            if message.message_kind != MessageKind.SYSTEM
        ]

    def to_anthropic_chat_system_message(self) -> str:
        system_messages = [
            message.content
            for message in self.messages
            if message.message_kind == MessageKind.SYSTEM
        ]
        return "\n".join(system_messages)
