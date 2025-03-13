import pytest
from openai.types.chat import ChatCompletionMessage, ParsedChatCompletionMessage
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind


@pytest.fixture
def llm_message() -> LlmMessage:
    return LlmMessage(content="Hello, world!", message_kind=MessageKind.USER)


@pytest.fixture
def openai_parsed_chat_completion_message() -> ParsedChatCompletionMessage:
    return ParsedChatCompletionMessage(
        content="Hello, world! - openai parsed chat completion",
        role="assistant",
    )


@pytest.fixture
def openai_chat_completion_message() -> ChatCompletionMessage:
    return ChatCompletionMessage(
        content="Hello, world! - openai chat completion",
        role="assistant",
    )


def test_llm_message_to_string(llm_message: LlmMessage) -> None:
    assert llm_message.content == "Hello, world!"
    assert llm_message.message_kind == MessageKind.USER


def test_to_persistent_llm_message(llm_message: LlmMessage) -> None:
    runtime_llm_message = llm_message.to_runtime_llm_message()
    assert runtime_llm_message.llm_message_json["content"] == "Hello, world!"
    assert runtime_llm_message.llm_message_json["message_kind"] == MessageKind.USER


def test_from_runtime_llm_message(llm_message: LlmMessage) -> None:
    runtime_llm_message = llm_message.to_runtime_llm_message()
    assert runtime_llm_message.llm_message_json["content"] == "Hello, world!"
    assert runtime_llm_message.llm_message_json["message_kind"] == MessageKind.USER
    assert llm_message == LlmMessage.from_runtime_llm_message(runtime_llm_message)


def test_from_openai_chat_completion_message(
    openai_chat_completion_message: ChatCompletionMessage,
) -> None:
    llm_message = LlmMessage.from_openai_chat_completion_message(
        openai_chat_completion_message
    )
    assert llm_message.content == "Hello, world! - openai chat completion"
    assert llm_message.message_kind == MessageKind.ASSISTANT
