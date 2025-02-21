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
from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_kind import MessageKind


class LlmMessageHistory:
    """
    LlmMessageHistory is a container for sequential LlmMessage objects that represent
    a conversation or a sequence of instructions and responses. Each LlmMessage
    instance can have a message kind (e.g., system, user, assistant, developer, tool
    call request, or tool call response). This class allows adding new messages,
    removing duplicates, and converting the entire message history into different
    representations suitable for various OpenAI models and APIs.

    Attributes:
        messages (list[LlmMessage]): A list of messages, each of which may be from
            a user, an assistant, or other message kinds. The order of the messages
            in this list represents the chronological order of the conversation so far.
    """

    def __init__(self, messages: list[LlmMessage]):
        self.messages = []
        for message in messages:
            self.add_message(message, debug=True)

    def add_message(self, message: LlmMessage, debug: bool = True) -> None:
        """
        Adds a new LlmMessage to the message history, ensuring that an identical
        message (with the same content, kind, and tool requests) is not already
        present. If the message is of kind SYSTEM, it is inserted at the start of
        the list; otherwise, it is appended at the end.

        Duplicate messages are removed by comparing their content, their message kind,
        and any associated tool requests. This method also calls the to_console method
        on the new message to optionally print a debug output.

        Args:
            message (LlmMessage): The new message to add to the history.
            debug (bool, optional): If True, prints debug information about the
                message addition. Defaults to True.
        """
        # Remove any existing message with the same content, kind, and tool ids
        self.messages = [
            m
            for m in self.messages
            if not (
                m.content == message.content
                and m.message_kind == message.message_kind
                and m.tool_requests == message.tool_requests
            )
        ]

        if message.message_kind == MessageKind.SYSTEM:
            self.messages.insert(0, message)
        else:
            self.messages.append(message)
        message.to_console(debug)

    def to_openai_strict(self) -> list[ChatCompletionMessageParam]:
        """
        Converts the message history into a list of ChatCompletionMessageParam objects
        that can be processed by OpenAI's strict API. This strict API requires specific
        fields like role, content, and supports tool call messages with an explicit
        tool_call_id.

        This method uses a match statement to inspect the MessageKind of each LlmMessage
        and convert it appropriately into ChatCompletionMessageParam objects. Cases for
        system, assistant, developer, tool call request, tool call response, user, and
        iteration messages are included. TOOL_CALL_REQUEST messages, for example, are
        handled by creating a ChatCompletionAssistantMessageParam with tool call details.

        Returns:
            list[ChatCompletionMessageParam]: A list of messages converted to a format
            that the OpenAI strict API can understand. Each element in the returned list
            is a ChatCompletionMessageParam object with the appropriate fields populated.
        """
        messages: list[ChatCompletionMessageParam] = []
        for message in self.messages:
            match message.message_kind:
                case MessageKind.TOOL_CALL_RESPONSE:
                    message_dict: ChatCompletionToolMessageParam = (
                        ChatCompletionToolMessageParam(
                            role="tool",
                            content=message.content,
                            tool_call_id=message.tool_response.id,
                        )
                    )
                case MessageKind.ASSISTANT:
                    message_dict: ChatCompletionAssistantMessageParam = (
                        ChatCompletionAssistantMessageParam(
                            role="assistant",
                            content=message.content,
                            tool_calls=message.tool_requests,
                        )
                    )
                case MessageKind.DEVELOPER:
                    message_dict: ChatCompletionDeveloperMessageParam = (
                        ChatCompletionDeveloperMessageParam(
                            role="developer",
                            content=message.content,
                        )
                    )
                case MessageKind.TOOL_CALL_REQUEST:
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
                case MessageKind.SYSTEM:
                    message_dict: ChatCompletionSystemMessageParam = (
                        ChatCompletionSystemMessageParam(
                            role="system",
                            content=message.content,
                        )
                    )
                case MessageKind.USER:
                    message_dict: ChatCompletionUserMessageParam = (
                        ChatCompletionUserMessageParam(
                            role="user",
                            content=message.content,
                        )
                    )
                case MessageKind.PARSING_DESCRIPTION:
                    message_dict: ChatCompletionDeveloperMessageParam = (
                        ChatCompletionDeveloperMessageParam(
                            role="developer",
                            content=message.content,
                        )
                    )
                case MessageKind.ITERATION if not any(
                    m.message_kind == MessageKind.ITERATION
                    for m in self.messages[self.messages.index(message) + 1 :]
                ):
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
            messages.append(message_dict)

        return messages

    def to_openai_o3(self) -> list:
        """
        Converts the message history into a list suitable for a different
        OpenAI API variant we will call "O3". The logic is somewhat more relaxed
        compared to to_openai_strict but still requires mapping each LlmMessage
        to a recognized message format.

        This method uses a match statement to inspect each LlmMessage and
        create one of the following message parameter objects: ChatCompletionDeveloperMessageParam,
        ChatCompletionAssistantMessageParam, ChatCompletionUserMessageParam.
        Different message kinds are handled slightly differently, e.g., TOOL_CALL_RESPONSE
        messages become developer role messages with user content, while
        SYSTEM messages become developer role messages, etc.

        Returns:
            list: A list of OpenAI-compatible message parameter objects,
            each containing role and content fields, along with optional
            fields such as tool_calls when relevant.
        """
        messages = []
        for message in self.messages:
            match message.message_kind:
                case MessageKind.TOOL_CALL_RESPONSE:
                    message_dict = ChatCompletionDeveloperMessageParam(
                        role="user",
                        content=message.content,
                    )
                case MessageKind.SYSTEM:
                    message_dict = ChatCompletionDeveloperMessageParam(
                        role="developer",
                        content=message.content,
                    )
                case MessageKind.ASSISTANT:
                    message_dict = ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=message.content,
                        tool_calls=message.tool_requests,
                    )
                case MessageKind.DEVELOPER:
                    message_dict = ChatCompletionDeveloperMessageParam(
                        role="developer",
                        content=message.content,
                    )
                case MessageKind.TOOL_CALL_REQUEST:
                    message_dict = ChatCompletionAssistantMessageParam(
                        role="assistant", content=message.content
                    )
                case MessageKind.USER:
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                case MessageKind.PARSING_DESCRIPTION:
                    message_dict = ChatCompletionDeveloperMessageParam(
                        role="developer",
                        content=message.content,
                    )
                case MessageKind.ITERATION if not any(
                    m.message_kind == MessageKind.ITERATION
                    for m in self.messages[self.messages.index(message) + 1 :]
                ):
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
            messages.append(message_dict)

        return messages

    def to_openai_o1(self) -> list:
        """
        Converts the message history into a list suitable for another
        OpenAI API variant we will refer to as "O1". Each LlmMessage in
        the history is again mapped to a role-content-based message format;
        the difference here is in how certain message kinds are classified.

        TOOL_CALL_RESPONSE, SYSTEM, DEVELOPER, and some other message kinds are
        merged into user messages. Meanwhile, an ASSISTANT message preserves
        its assistant role but can optionally hold tool_calls.

        Returns:
            list: A list of OpenAI-compatible message parameter objects,
            each dict with role and content fields, and possibly tool_calls when
            relevant for the assistant role.
        """
        messages = []
        for message in self.messages:
            match message.message_kind:
                case MessageKind.TOOL_CALL_RESPONSE:
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                case MessageKind.SYSTEM:
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                case MessageKind.ASSISTANT:
                    message_dict = ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=message.content,
                        tool_calls=message.tool_requests,
                    )
                case MessageKind.DEVELOPER:
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                case MessageKind.TOOL_CALL_REQUEST:
                    message_dict = ChatCompletionAssistantMessageParam(
                        role="assistant", content=message.content
                    )
                case MessageKind.USER:
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                case MessageKind.PARSING_DESCRIPTION:
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
                case MessageKind.ITERATION if not any(
                    m.message_kind == MessageKind.ITERATION
                    for m in self.messages[self.messages.index(message) + 1 :]
                ):
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
            messages.append(message_dict)

        return messages

    def to_anthropic(self) -> tuple[str | None, list[dict]]:
        """
        Converts the message history into a format suitable for the Anthropic API.
        Returns a tuple of (combined system messages, regular messages list).
        System messages are combined into a single string since Anthropic only
        supports one system message.

        Returns:
            tuple[str | None, list[dict]]: A tuple containing:
                - Combined system message content (or None if no system messages)
                - List of regular messages in Anthropic format
        """
        messages = []
        system_messages = []

        for message in self.messages:
            match message.message_kind:
                case MessageKind.SYSTEM | MessageKind.PARSING_DESCRIPTION:
                    # Collect all system messages
                    if message.content:
                        system_messages.append(message.content)
                case MessageKind.ASSISTANT:
                    message_dict = {
                        "role": "assistant",
                        "content": message.content,
                    }
                    messages.append(message_dict)
                case MessageKind.USER | MessageKind.DEVELOPER | MessageKind.ITERATION:
                    message_dict = {
                        "role": "user",
                        "content": message.content,
                    }
                    messages.append(message_dict)
                case MessageKind.TOOL_CALL_REQUEST:
                    message_dict = {
                        "role": "assistant",
                        "content": message.content,
                    }
                    messages.append(message_dict)
                case MessageKind.TOOL_CALL_RESPONSE:
                    message_dict = {
                        "role": "user",
                        "content": message.content,
                    }
                    messages.append(message_dict)

        # Combine system messages if any exist
        combined_system = "\n\n".join(system_messages) if system_messages else None

        return messages, combined_system
