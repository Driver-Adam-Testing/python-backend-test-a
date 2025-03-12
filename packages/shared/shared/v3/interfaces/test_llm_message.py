import pytest
from anthropic.types import Message, MessageParam, TextBlock
from database.models_v2 import RuntimeLlmMessage
from openai.types.chat import (
    ChatCompletionMessage,
    ParsedChatCompletionMessage,
)
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion_message_tool_call import (
    Function as ToolCallFunction,
)
from openai.types.chat.parsed_function_tool_call import (
    ParsedFunction,
    ParsedFunctionToolCall,
)
from pydantic import BaseModel
from shared.v3 import LlmMessage, LlmResponseType, LlmTool, MessageKind
from shared.v3.globals.constants import PARSEABLE_CLASS_NAME


@pytest.fixture
def user_message() -> LlmMessage:
    return LlmMessage(message_kind=MessageKind.USER, content="Hello, world!")


@pytest.fixture
def assistant_message() -> LlmMessage:
    return LlmMessage(message_kind=MessageKind.ASSISTANT, content="Hello, world!")


@pytest.fixture
def system_message() -> LlmMessage:
    return LlmMessage(message_kind=MessageKind.SYSTEM, content="Hello, world!")


@pytest.fixture
def tool_message() -> LlmMessage:
    return LlmMessage(message_kind=MessageKind.TOOL, content="Hello, world!")


@pytest.fixture
def tool_response_message() -> LlmMessage:
    return LlmMessage(message_kind=MessageKind.TOOL_RESPONSE, content="Hello, world!")


@pytest.fixture
def tool_request_message() -> LlmMessage:
    return LlmMessage(message_kind=MessageKind.TOOL_REQUEST, content="Hello, world!")


@pytest.fixture
def tool_type() -> type[LlmTool]:
    class TestTool(LlmTool):
        arg1: str

        def _execute(self) -> LlmMessage:
            return LlmMessage(
                message_kind=MessageKind.ASSISTANT, content="Hello, world!"
            )

        @property
        def to_tool_call_response_message(self) -> LlmMessage:
            return LlmMessage(
                message_kind=MessageKind.TOOL_RESPONSE, content="Hello, world!"
            )

    return TestTool


@pytest.fixture
def response_type() -> type[LlmResponseType]:
    class TestResponse(LlmResponseType):
        result: str

    return TestResponse


def test_llm_message_to_persistent_llm_message(user_message: LlmMessage) -> None:
    persistent_message: RuntimeLlmMessage = user_message.to_persistent_llm_message()
    assert persistent_message.llm_message_json == user_message.model_dump()


def test_from_runtime_llm_message() -> None:
    original_message = LlmMessage(message_kind=MessageKind.USER, content="Test message")
    persistent_message = original_message.to_persistent_llm_message()
    recreated_message = LlmMessage.from_runtime_llm_message(persistent_message)
    assert recreated_message.message_kind == original_message.message_kind
    assert recreated_message.content == original_message.content


def test_from_openai_parsed_chat_completion_message(
    tool_type: type[LlmTool], response_type: type[LlmResponseType]
) -> None:
    # Create a mock ParsedChatCompletionMessage

    # Tool call scenario
    parsed_tool_call = ParsedFunctionToolCall(
        id="call_123",
        function=ParsedFunction(
            name="test_function",
            arguments='{"arg1": "value1"}',
            parsed_arguments={"arg1": "value1"},
        ),
        type="function",
    )

    parsed_message_tool = ParsedChatCompletionMessage(
        content="Test content for tool call",
        tool_calls=[parsed_tool_call],
        parsed={"key": "value"},
        role="assistant",
        refusal="Test refusal",
        audio=None,
        function_call=None,
    )

    message_tool = LlmMessage.from_openai_parsed_chat_completion_message(
        parsed_message_tool
    )

    assert message_tool.message_kind == MessageKind.TOOL_CALL_REQUEST
    assert message_tool.content == "Test content for tool call"
    # Updated assertion to match the parsed dictionary instead of the response_type
    assert message_tool.parsed_content == {"key": "value"}
    assert len(message_tool.tool_requests) == 1
    assert message_tool.tool_requests[0].id == "call_123"
    assert message_tool.tool_requests[0].name == "test_function"
    assert message_tool.tool_requests[0].arguments == '{"arg1": "value1"}'
    assert message_tool.tool_requests[0].parsed_tool == tool_type(arg1="value1")

    # Standard response scenario
    parsed_message_response = ParsedChatCompletionMessage(
        content="Test content for standard response",
        tool_calls=[],
        parsed={"key": "value"},
        role="assistant",
        refusal="Test refusal",
        audio=None,
        function_call=None,
    )

    message_response = LlmMessage.from_openai_parsed_chat_completion_message(
        parsed_message_response
    )

    assert message_response.message_kind == MessageKind.ASSISTANT
    assert message_response.content == "Test content for standard response"
    # Updated assertion to match the parsed dictionary instead of the response_type
    assert message_response.parsed_content == {"key": "value"}
    assert len(message_response.tool_requests) == 0


def test_from_openai_chat_completion_message(tool_type: type[LlmTool]) -> None:
    class TestResponse(LlmResponseType):
        result: str

    # Test with tool calls
    tool_call = ChatCompletionMessageToolCall(
        id="call_123",
        function=ToolCallFunction(name="TestTool", arguments='{"arg1": "value1"}'),
        type="function",
    )

    chat_message = ChatCompletionMessage(
        content=None, role="assistant", tool_calls=[tool_call]
    )

    message = LlmMessage.from_openai_chat_completion_message(
        chat_message=chat_message, tool_types=[tool_type]
    )

    assert message.message_kind == MessageKind.TOOL_CALL_REQUEST
    assert len(message.tool_requests) == 1
    assert message.tool_requests[0].id == "call_123"
    assert message.tool_requests[0].name == "TestTool"
    assert isinstance(message.tool_requests[0].parsed_tool, tool_type)

    # Test with content that can be parsed as response
    chat_message = ChatCompletionMessage(
        content='{"result": "success"}', role="assistant"
    )

    message = LlmMessage.from_openai_chat_completion_message(
        chat_message=chat_message, response_type=TestResponse
    )

    assert message.message_kind == MessageKind.ASSISTANT
    assert message.content == '{"result": "success"}'
    assert isinstance(message.parsed_content, TestResponse)
    assert message.parsed_content.result == "success"


def test_from_string(
    tool_type: type[LlmTool], response_type: type[LlmResponseType]
) -> None:
    # Test with tool request in string
    tool_request_str = f'{{"arg1": "value1", "{PARSEABLE_CLASS_NAME}": "TestTool", "id": "123", "arguments": "test"}}'

    message = LlmMessage.from_string(string=tool_request_str, tool_types=[tool_type])

    assert message.message_kind == MessageKind.TOOL_CALL_REQUEST
    assert len(message.tool_requests) == 1
    assert message.tool_requests[0].name == "TestTool"
    assert message.tool_requests[0].id == "123"
    assert isinstance(message.tool_requests[0].parsed_tool, tool_type)

    # Test with regular content that can be parsed as response
    response_str = '{"result": "success"}'

    message = LlmMessage.from_string(string=response_str, response_type=response_type)

    assert message.message_kind == MessageKind.ASSISTANT
    assert message.content == response_str
    assert isinstance(message.parsed_content, response_type)
    assert message.parsed_content.result == "success"


def test_from_anthropic_message(tool_type: type[LlmTool]) -> None:
    class TestResponse(BaseModel):
        result: str

    # Test with Message object
    content_block = TextBlock(text='{"result": "success"}', type="text")
    message_obj = Message(
        content=[content_block],
        role="assistant",
        id="msg_123",
        model="claude-3-opus-20240229",
        type="message",
        usage={"input_tokens": 10, "output_tokens": 20},
    )

    message = LlmMessage.from_anthropic_message(
        message=message_obj, response_type=TestResponse
    )

    assert message.message_kind == MessageKind.ASSISTANT
    assert message.content == '{"result": "success"}'
    assert isinstance(message.parsed_content, TestResponse)
    assert message.parsed_content.result == "success"

    # Test with MessageParam object
    message_param = MessageParam(
        content=f'{{"arg1": "value1", "{PARSEABLE_CLASS_NAME}": "TestTool"}}',
        role="assistant",
    )

    message = LlmMessage.from_anthropic_message(
        message=message_param, tool_types=[tool_type]
    )

    assert message.message_kind == MessageKind.TOOL_CALL_REQUEST
    assert (
        message.content == f'{{"arg1": "value1", "{PARSEABLE_CLASS_NAME}": "TestTool"}}'
    )
    assert len(message.tool_requests) == 1
    assert message.tool_requests[0].name == "TestTool"
    assert isinstance(message.tool_requests[0].parsed_tool, tool_type)


def test_hash() -> None:
    message1 = LlmMessage(message_kind=MessageKind.USER, content="Hello")
    message2 = LlmMessage(message_kind=MessageKind.USER, content="Hello")
    message3 = LlmMessage(message_kind=MessageKind.USER, content="Different")

    assert hash(message1) == hash(message2)
    assert hash(message1) != hash(message3)


def test_print_to_console(capsys) -> None:
    message = LlmMessage(message_kind=MessageKind.USER, content="Test message")
    message.print_to_console()

    captured = capsys.readouterr()
    assert "USER" in captured.out
    assert "Test message" in captured.out

    # Test with tool requests
    tool_request = LlmMessage.ToolCallRequest(
        id="call_123", name="test_function", arguments='{"arg1": "value1"}'
    )

    message = LlmMessage(
        message_kind=MessageKind.TOOL_CALL_REQUEST,
        content="Test with tool",
        tool_requests=[tool_request],
    )

    message.print_to_console()
    captured = capsys.readouterr()
    assert "TOOL_CALL_REQUEST" in captured.out
    assert "Tool Requests:" in captured.out
    assert "call_123" in captured.out
    assert "test_function" in captured.out
