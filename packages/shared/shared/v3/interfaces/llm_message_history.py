from uuid import UUID

from database.db import get_session
from database.models_v2 import (
    RuntimeLlmMessage,
    RuntimeLlmMessageHistory,
)
from database.models_v2_enums import LlmPipelineKind
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
from sqlalchemy.orm import selectinload
from sqlmodel import delete, select


class LlmMessageHistory:
    """
    LlmMessageHistory is a container for sequential LlmMessage objects that represent
    a conversation or a sequence of instructions and responses.
    """

    def __init__(
        self,
        messages: list[LlmMessage] | None = None,
        id: UUID | None = None,
        llm_session_id: UUID | None = None,
        pipeline_kind: LlmPipelineKind = LlmPipelineKind.DEFAULT,
        debug: bool = True,
    ) -> None:
        self.id = id
        self.llm_session_id = llm_session_id
        self.pipeline_kind = pipeline_kind
        self.debug = debug

        if id is None and llm_session_id is not None:
            with get_session() as session:
                llm_message_history = RuntimeLlmMessageHistory(
                    llm_session_id=llm_session_id,
                    pipeline_kind=pipeline_kind,
                )
                session.add(llm_message_history)
                session.commit()
                session.refresh(llm_message_history)
                self.id = llm_message_history.id

        self.messages: list[LlmMessage] = []
        if messages:
            for message in messages:
                self.add_message(message, debug=debug)

    @classmethod
    def from_db(
        cls,
        message_history_id: UUID,
    ) -> "LlmMessageHistory":
        """
        Loads the message history from the database.
        """
        with get_session() as session:
            runtime_llm_message_history: RuntimeLlmMessageHistory = session.exec(
                select(RuntimeLlmMessageHistory)
                .where(RuntimeLlmMessageHistory.id == message_history_id)
                .options(selectinload(RuntimeLlmMessageHistory.messages))
            ).first()
            if runtime_llm_message_history is None:
                raise ValueError(
                    f"Message history with id {message_history_id} not found"
                )
            message_history = cls(
                messages=[],
                id=runtime_llm_message_history.id,
                llm_session_id=runtime_llm_message_history.llm_session_id,
                pipeline_kind=runtime_llm_message_history.pipeline_kind,
            )
            message_history.messages = [
                LlmMessage(**message.llm_message_json)
                for message in runtime_llm_message_history.messages
            ]
            return message_history

    def add_message(
        self, message: LlmMessage, debug: bool = True
    ) -> "LlmMessageHistory":
        # TODO: Would it make sense to automatically yield messages that make sense to yield here? Ignore them if we aren't in a streaming context?
        """
        Adds a new LlmMessage to the history.
        """
        if hash(message) in {hash(m) for m in self.messages}:
            return
        self.messages.append(message)
        if self.llm_session_id and self.id and message.persist:
            pm = RuntimeLlmMessage(
                llm_message_json=message.model_dump(),
                llm_message_hash=hash(message),
                message_history_id=self.id,
            )
            with get_session() as session:
                session.add(pm)
                session.commit()
                session.refresh(pm)
        if debug:
            message.print_to_console()
        return self

    def remove_message(self, message: LlmMessage) -> None:
        """
        Removes a LlmMessage from the history.
        """
        self.messages.remove(message)
        if self.llm_session_id and self.id and message.persist:
            with get_session() as session:
                session.exec(
                    delete(RuntimeLlmMessage)
                    .where(
                        RuntimeLlmMessage.llm_message_json == message.model_dump_json()
                    )
                    .where(RuntimeLlmMessage.message_history_id == self.id)
                )
                session.commit()

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
                            tool_calls=message.tool_requests
                            if len(message.tool_requests) > 0
                            else None,
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
                case MessageKind.ITERATION:
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
                case MessageKind.ITERATION:
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
                case MessageKind.ITERATION:
                    message_dict = ChatCompletionUserMessageParam(
                        role="user",
                        content=message.content,
                    )
            messages.append(message_dict)

        return messages

    def to_anthropic(self) -> tuple[list[dict], str | None]:
        """
        Converts the message history into a format suitable for the Anthropic API.
        Returns a tuple of (regular messages list, combined system messages).
        System messages are combined into a single string since Anthropic only
        supports one system message.

        Returns:
            tuple[list[dict], str | None]: A tuple containing:
                - List of regular messages in Anthropic format
                - Combined system message content (or None if no system messages)
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
                case MessageKind.USER | MessageKind.DEVELOPER:
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
                case MessageKind.ITERATION:
                    message_dict = {
                        "role": "user",
                        "content": message.content,
                    }
                    messages.append(message_dict)

        # Combine system messages if any exist
        combined_system_message_content = (
            "\n\n".join(system_messages) if system_messages else None
        )

        return messages, combined_system_message_content

    def _remove_iteration_messages(self) -> None:
        """
        Removes all iteration messages from the message history.
        """
        for message in self.messages:
            if message.message_kind == MessageKind.ITERATION:
                self.remove_message(message)

    def _remove_parsing_description_messages(self) -> None:
        """
        Removes all parsing description messages from the message history.
        """
        for message in self.messages:
            if message.message_kind == MessageKind.PARSING_DESCRIPTION:
                self.remove_message(message)

    def clean(self) -> None:
        """
        Removes all iteration and parsing description messages from the message history.
        """
        self._remove_iteration_messages()
        self._remove_parsing_description_messages()

    def copy(self) -> "LlmMessageHistory":
        """
        Creates a deep copy of the LlmMessageHistory instance.

        Returns:
            LlmMessageHistory: A new instance of LlmMessageHistory with copied messages.
        """
        copied_messages = [message.model_copy() for message in self.messages]
        return LlmMessageHistory(messages=copied_messages, debug=False)

    def last(self) -> LlmMessage:
        """
        Returns the last message in the message history.
        """
        return self.messages[-1]
